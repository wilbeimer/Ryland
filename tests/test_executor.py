from uuid import uuid4
import pytest
from backend.ai.curriculum_agent.executor import (
    create_week
)
from backend.models import Course, CurriculumRequest, RylandState


def make_state() -> RylandState:
    return RylandState(request=CurriculumRequest(name="Test", color="#FFFF", description="Test Course"), course=Course(str(uuid4()), "Test", "#FFFF"))


def test_create_week_success():
    state = make_state()
    result = create_week(state, week_number=1, goal="Learn X", topics=["a", "b"])
    assert result['status'] == "ok"
    assert len(state.course.weeks) == 1
    assert state.course.weeks[0].number == 1
    assert state.course.weeks[0].goal == "Learn X"


def test_create_week_duplicate_fails():
    state = make_state()
    create_week(state, week_number=1, goal="Learn X", topics=["a"])
    result = create_week(state, week_number=1, goal="Learn Y", topics=["b"])
    assert "error" in result
    assert len(state.course.weeks) == 1  # second call didn't mutate


def test_create_week_sorts_out_of_order():
    state = make_state()
    create_week(state, week_number=2, goal="B", topics=[])
    create_week(state, week_number=1, goal="A", topics=[])
    assert [w.number for w in state.course.weeks] == [1, 2]
