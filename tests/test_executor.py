"""
Tests for backend.ai.curriculum_agent.executor

Covers:
- All tool functions (set_course_*, create_week, create_assignment, create_quiz, search_youtube, finish_course)
- Happy path and error cases
- State mutations and validation
- Lookup behavior (_find_week)
"""
import pytest
import uuid
from unittest.mock import patch

from backend.models import (
    RylandState,
    CurriculumRequest,
    Course,
    Week,
    AssignmentType,
    QuizType,
    ResourceSource,
    Textbook,
    CourseStatus,
)


@pytest.fixture
def executor():
    """Lazy-load executor to allow test execution without the module present."""
    from backend.ai.curriculum_agent import executor as exec_module
    return exec_module


@pytest.fixture
def base_state():
    """Create a fresh RylandState for each test."""
    request = CurriculumRequest(name="Test Course", color="blue", description="A test course")
    course = Course(id=str(uuid.uuid4()), name="Test Course", color="blue")
    return RylandState(request=request, course=course)


class TestFindWeek:
    def test_find_week_exists(self, base_state, executor):
        week = Week(id="w1", number=1, goal="Learn basics", topics=["intro"])
        base_state.course.weeks.append(week)
        found = executor._find_week(base_state, 1)
        assert found is week

    def test_find_week_not_exists(self, base_state, executor):
        found = executor._find_week(base_state, 1)
        assert found is None

    def test_find_week_multiple_weeks(self, base_state, executor):
        w1 = Week(id="w1", number=1, goal="Week 1", topics=["a"])
        w2 = Week(id="w2", number=2, goal="Week 2", topics=["b"])
        w3 = Week(id="w3", number=3, goal="Week 3", topics=["c"])
        base_state.course.weeks = [w1, w2, w3]
        assert executor._find_week(base_state, 2) is w2


class TestSetCourseDescription:
    def test_set_description_only(self, base_state, executor):
        result = executor.set_course_description(
            base_state, description="Updated description"
        )
        assert result == {"status": "ok"}
        assert base_state.course.description == "Updated description"

    def test_set_all_fields(self, base_state, executor):
        result = executor.set_course_description(
            base_state,
            description="New desc",
            domain="Computer Science",
            subdomains=["AI", "ML"],
            prerequisites=["Python", "Math"],
        )
        assert result == {"status": "ok"}
        assert base_state.course.description == "New desc"
        assert base_state.course.domain == "Computer Science"
        assert base_state.course.subdomains == ["AI", "ML"]
        assert base_state.course.prerequisites == ["Python", "Math"]

    def test_set_partial_fields(self, base_state, executor):
        executor.set_course_description(
            base_state,
            description="Desc",
            domain="CS",
        )
        assert base_state.course.description == "Desc"
        assert base_state.course.domain == "CS"
        assert base_state.course.subdomains == []
        assert base_state.course.prerequisites == []

    def test_description_empty_string(self, base_state, executor):
        result = executor.set_course_description(base_state, description="")
        assert result == {"status": "ok"}
        assert base_state.course.description == ""


class TestSetCourseLength:
    def test_set_course_length_success(self, base_state, executor):
        result = executor.set_course_length(base_state, duration_weeks=12, hours_per_week=5)
        assert result == {"status": "ok"}
        assert base_state.course.duration_weeks == 12
        assert base_state.course.hours_per_week == 5

    def test_set_course_length_overwrites(self, base_state, executor):
        base_state.course.duration_weeks = 8
        base_state.course.hours_per_week = 3
        executor.set_course_length(base_state, duration_weeks=16, hours_per_week=10)
        assert base_state.course.duration_weeks == 16
        assert base_state.course.hours_per_week == 10

    def test_set_course_length_zero_weeks(self, base_state, executor):
        result = executor.set_course_length(base_state, duration_weeks=0, hours_per_week=5)
        assert result == {"status": "ok"}
        assert base_state.course.duration_weeks == 0

    def test_set_course_length_decimal_hours(self, base_state, executor):
        result = executor.set_course_length(base_state, duration_weeks=10, hours_per_week=2.5)
        assert result == {"status": "ok"}
        assert base_state.course.hours_per_week == 2.5


class TestSetTextbook:
    def test_set_textbook_minimal(self, base_state, executor):
        result = executor.set_textbook(
            base_state,
            title="Python Basics",
            authors=["John Doe"],
        )
        assert result == {"status": "ok"}
        assert base_state.course.textbook is not None
        assert base_state.course.textbook.title == "Python Basics"
        assert base_state.course.textbook.authors == ["John Doe"]

    def test_set_textbook_full(self, base_state, executor):
        result = executor.set_textbook(
            base_state,
            title="Advanced Python",
            authors=["Jane Doe", "John Smith"],
            edition="3rd",
            publisher="Tech Press",
            isbn="978-1234567890",
            link="https://example.com/book",
        )
        assert result == {"status": "ok"}
        tb = base_state.course.textbook
        assert tb.title == "Advanced Python"
        assert tb.authors == ["Jane Doe", "John Smith"]
        assert tb.edition == "3rd"
        assert tb.publisher == "Tech Press"
        assert tb.isbn == "978-1234567890"
        assert tb.link == "https://example.com/book"

    def test_set_textbook_overwrites(self, base_state, executor):
        old_tb = Textbook(title="Old Book", authors=["Old Author"])
        base_state.course.textbook = old_tb
        executor.set_textbook(
            base_state,
            title="New Book",
            authors=["New Author"],
        )
        assert base_state.course.textbook.title == "New Book"

    def test_set_textbook_multiple_authors(self, base_state, executor):
        result = executor.set_textbook(
            base_state,
            title="Collaborative Work",
            authors=["Author A", "Author B", "Author C"],
        )
        assert result == {"status": "ok"}
        assert len(base_state.course.textbook.authors) == 3


class TestCreateWeek:
    def test_create_week_success(self, base_state, executor):
        result = executor.create_week(
            base_state, week_number=1, goal="Learn basics", topics=["intro", "setup"]
        )
        assert result["status"] == "ok"
        assert "week_id" in result
        assert len(base_state.course.weeks) == 1
        assert base_state.course.weeks[0].number == 1
        assert base_state.course.weeks[0].goal == "Learn basics"
        assert base_state.course.weeks[0].topics == ["intro", "setup"]

    def test_create_week_duplicate_fails(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Week 1", topics=["a"])
        result = executor.create_week(base_state, week_number=1, goal="Week 1 again", topics=["b"])
        assert "error" in result
        assert "already exists" in result["error"]
        assert len(base_state.course.weeks) == 1

    def test_create_week_sorts_out_of_order(self, base_state, executor):
        executor.create_week(base_state, week_number=3, goal="Week 3", topics=["c"])
        executor.create_week(base_state, week_number=1, goal="Week 1", topics=["a"])
        executor.create_week(base_state, week_number=2, goal="Week 2", topics=["b"])
        assert [w.number for w in base_state.course.weeks] == [1, 2, 3]

    def test_create_week_empty_topics(self, base_state, executor):
        result = executor.create_week(base_state, week_number=1, goal="Goal", topics=[])
        assert result["status"] == "ok"
        assert base_state.course.weeks[0].topics == []

    def test_create_week_ids_unique(self, base_state, executor):
        r1 = executor.create_week(base_state, week_number=1, goal="W1", topics=["a"])
        r2 = executor.create_week(base_state, week_number=2, goal="W2", topics=["b"])
        assert r1["week_id"] != r2["week_id"]


class TestCreateAssignment:
    def test_create_assignment_success(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_assignment(
            base_state,
            week_number=1,
            title="Essay",
            type="written",
            description="Write an essay",
            requirements=["1000 words", "APA format"],
            points=50,
            rubric="Content (25%), Style (25%)",
        )
        assert result["status"] == "ok"
        assert "assignment_id" in result
        week = base_state.course.weeks[0]
        assert len(week.assignments) == 1
        assert week.assignments[0].title == "Essay"
        assert week.assignments[0].type == AssignmentType.WRITTEN
        assert week.assignments[0].points == 50

    def test_create_assignment_no_week_fails(self, base_state, executor):
        result = executor.create_assignment(
            base_state,
            week_number=1,
            title="Essay",
            type="written",
            description="Write",
        )
        assert "error" in result
        assert "No week 1 yet" in result["error"]

    def test_create_assignment_all_types(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        types = ["written", "checklist", "project", "presentation"]
        for atype in types:
            result = executor.create_assignment(
                base_state,
                week_number=1,
                title=f"Assignment {atype}",
                type=atype,
                description="Test",
            )
            assert result["status"] == "ok"
        assert len(base_state.course.weeks[0].assignments) == 4

    def test_create_assignment_invalid_type(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_assignment(
            base_state,
            week_number=1,
            title="Bad",
            type="invalid_type",
            description="Test",
        )
        assert "error" in result

    def test_create_assignment_with_resources(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_assignment(
            base_state,
            week_number=1,
            title="Reading",
            type="written",
            description="Read and summarize",
            resources=[
                {"title": "Article 1", "url": "https://example.com/1", "source": "article"},
                {"title": "Video 1", "url": "https://youtube.com/watch?v=xyz", "source": "youtube"},
            ],
        )
        assert result["status"] == "ok"
        assignment = base_state.course.weeks[0].assignments[0]
        assert len(assignment.resources) == 2
        assert assignment.resources[0].source == ResourceSource.ARTICLE
        assert assignment.resources[1].source == ResourceSource.YOUTUBE

    def test_create_assignment_default_source(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_assignment(
            base_state,
            week_number=1,
            title="Test",
            type="written",
            description="Test",
            resources=[{"title": "Res", "url": "https://example.com"}],
        )
        assert result["status"] == "ok"
        assert base_state.course.weeks[0].assignments[0].resources[0].source == ResourceSource.ARTICLE

    def test_create_assignment_missing_required_resource_fields(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_assignment(
            base_state,
            week_number=1,
            title="Test",
            type="written",
            description="Test",
            resources=[{"title": "No URL"}],
        )
        assert "error" in result

    def test_create_assignment_empty_requirements(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_assignment(
            base_state,
            week_number=1,
            title="Test",
            type="written",
            description="Test",
        )
        assert result["status"] == "ok"
        assert base_state.course.weeks[0].assignments[0].requirements == []

    def test_create_assignment_default_points(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        executor.create_assignment(
            base_state,
            week_number=1,
            title="Test",
            type="written",
            description="Test",
        )
        assert base_state.course.weeks[0].assignments[0].points == 100

    def test_create_assignment_ids_unique(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        r1 = executor.create_assignment(
            base_state, week_number=1, title="A1", type="written", description="T1"
        )
        r2 = executor.create_assignment(
            base_state, week_number=1, title="A2", type="written", description="T2"
        )
        assert r1["assignment_id"] != r2["assignment_id"]


class TestCreateQuiz:
    def test_create_quiz_success(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_quiz(
            base_state,
            week_number=1,
            title="Week 1 Quiz",
            type="weekly",
            questions=[
                {
                    "type": "multiple_choice",
                    "prompt": "What is 2+2?",
                    "choices": ["3", "4", "5"],
                    "answer": "4",
                },
                {
                    "type": "short_answer",
                    "prompt": "Explain X",
                    "answer": "X is...",
                },
            ],
            points=20,
        )
        assert result["status"] == "ok"
        assert "quiz_id" in result
        week = base_state.course.weeks[0]
        assert week.quiz is not None
        assert week.quiz.title == "Week 1 Quiz"
        assert len(week.quiz.questions) == 2
        assert week.quiz.points == 20

    def test_create_quiz_no_week_fails(self, base_state, executor):
        result = executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz",
            type="weekly",
            questions=[],
        )
        assert "error" in result
        assert "No week 1 yet" in result["error"]

    def test_create_quiz_duplicate_fails(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz 1",
            type="weekly",
            questions=[
                {"type": "multiple_choice", "prompt": "Q1", "choices": ["A", "B"], "answer": "A"}
            ],
        )
        result = executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz 2",
            type="weekly",
            questions=[
                {"type": "multiple_choice", "prompt": "Q2", "choices": ["A", "B"], "answer": "B"}
            ],
        )
        assert "error" in result
        assert "already has a quiz" in result["error"]

    def test_create_quiz_replace_true(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz 1",
            type="weekly",
            questions=[
                {"type": "multiple_choice", "prompt": "Q1", "choices": ["A", "B"], "answer": "A"}
            ],
        )
        result = executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz 2",
            type="review",
            questions=[
                {"type": "multiple_choice", "prompt": "Q2", "choices": ["A", "B"], "answer": "B"}
            ],
            replace=True,
        )
        assert result["status"] == "ok"
        assert base_state.course.weeks[0].quiz.title == "Quiz 2"
        assert base_state.course.weeks[0].quiz.type == QuizType.REVIEW

    def test_create_quiz_all_types(self, base_state, executor):
        quiz_types = ["weekly", "midterm", "final", "review"]
        for i, qtype in enumerate(quiz_types):
            executor.create_week(base_state, week_number=i + 1, goal="Goal", topics=["a"])
            result = executor.create_quiz(
                base_state,
                week_number=i + 1,
                title=f"Quiz {qtype}",
                type=qtype,
                questions=[
                    {"type": "multiple_choice", "prompt": "Q", "choices": ["A"], "answer": "A"}
                ],
            )
            assert result["status"] == "ok"

    def test_create_quiz_multiple_questions(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        questions = [
            {"type": "multiple_choice", "prompt": "Q1", "choices": ["A", "B"], "answer": "A"},
            {"type": "short_answer", "prompt": "Q2", "answer": "Answer"},
            {"type": "multiple_choice", "prompt": "Q3", "choices": ["X", "Y", "Z"], "answer": "Y"},
        ]
        result = executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz",
            type="weekly",
            questions=questions,
        )
        assert result["status"] == "ok"
        assert len(base_state.course.weeks[0].quiz.questions) == 3

    def test_create_quiz_invalid_type(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz",
            type="invalid_quiz_type",
            questions=[],
        )
        assert "error" in result

    def test_create_quiz_invalid_question_type(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz",
            type="weekly",
            questions=[
                {"type": "bad_type", "prompt": "Q", "answer": "A"}
            ],
        )
        assert "error" in result

    def test_create_quiz_missing_question_field(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_quiz(
            base_state,
            week_number=1,
            title="Quiz",
            type="weekly",
            questions=[
                {"type": "multiple_choice", "choices": ["A", "B"]}
            ],
        )
        assert "error" in result


class TestSearchYoutube:
    @patch("backend.ai.curriculum_agent.executor._search_youtube_api")
    def test_search_youtube_success(self, mock_yt, base_state, executor):
        mock_yt.return_value = [
            {"title": "Video 1", "url": "https://youtube.com/v1", "channel": "Channel A"},
            {"title": "Video 2", "url": "https://youtube.com/v2", "channel": "Channel B"},
        ]
        result = executor.search_youtube(base_state, query="Python tutorial", max_results=2)
        assert "results" in result
        assert len(result["results"]) == 2
        mock_yt.assert_called_once_with("Python tutorial", max_results=2)

    @patch("backend.ai.curriculum_agent.executor._search_youtube_api")
    def test_search_youtube_default_max_results(self, mock_yt, base_state, executor):
        mock_yt.return_value = []
        executor.search_youtube(base_state, query="Test")
        mock_yt.assert_called_once_with("Test", max_results=2)

    @patch("backend.ai.curriculum_agent.executor._search_youtube_api")
    def test_search_youtube_empty_results(self, mock_yt, base_state, executor):
        mock_yt.return_value = []
        result = executor.search_youtube(base_state, query="Obscure term xyz")
        assert "results" in result
        assert result["results"] == []

    @patch("backend.ai.curriculum_agent.executor._search_youtube_api")
    def test_search_youtube_api_error(self, mock_yt, base_state, executor):
        mock_yt.side_effect = Exception("API rate limit exceeded")
        result = executor.search_youtube(base_state, query="Test")
        assert "error" in result
        assert "YouTube search failed" in result["error"]


class TestFinishCourse:
    def test_finish_course_success(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        executor.create_assignment(
            base_state, week_number=1, title="A", type="written", description="D"
        )
        result = executor.finish_course(base_state)
        assert result["status"] == "complete"
        assert result["week_count"] == 1
        assert base_state.course.status == CourseStatus.COMPLETE

    def test_finish_course_multiple_weeks(self, base_state, executor):
        for i in range(1, 4):
            executor.create_week(base_state, week_number=i, goal=f"Goal {i}", topics=["a"])
            executor.create_assignment(
                base_state, week_number=i, title=f"A{i}", type="written", description="D"
            )
        result = executor.finish_course(base_state)
        assert result["status"] == "complete"
        assert result["week_count"] == 3

    def test_finish_course_no_weeks(self, base_state, executor):
        result = executor.finish_course(base_state)
        assert "error" in result
        assert "no weeks created" in result["error"]

    def test_finish_course_week_no_assignments(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        executor.create_week(base_state, week_number=2, goal="Goal", topics=["a"])
        executor.create_assignment(
            base_state, week_number=1, title="A1", type="written", description="D"
        )
        result = executor.finish_course(base_state)
        assert "error" in result
        assert "week 2 has no assignments" in result["error"]

    def test_finish_course_multiple_errors(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.finish_course(base_state)
        assert "error" in result
        assert "week 1 has no assignments" in result["error"]


class TestExecuteTool:
    def test_execute_tool_success(self, base_state, executor):
        result = executor.execute_tool(
            "set_course_length",
            {"duration_weeks": 10, "hours_per_week": 5},
            base_state,
        )
        assert result["status"] == "ok"
        assert base_state.course.duration_weeks == 10

    def test_execute_tool_unknown_tool(self, base_state, executor):
        result = executor.execute_tool(
            "unknown_tool",
            {},
            base_state,
        )
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_execute_tool_bad_arguments(self, base_state, executor):
        result = executor.execute_tool(
            "set_course_length",
            {"duration_weeks": 10},  # Missing hours_per_week
            base_state,
        )
        assert "error" in result
        assert "Bad arguments" in result["error"]

    def test_execute_tool_via_dispatcher(self, base_state, executor):
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.execute_tool(
            "create_assignment",
            {
                "week_number": 1,
                "title": "Essay",
                "type": "written",
                "description": "Write an essay",
            },
            base_state,
        )
        assert result["status"] == "ok"
        assert len(base_state.course.weeks[0].assignments) == 1


class TestIntegration:
    """End-to-end scenarios testing multiple tool calls in sequence."""

    def test_full_curriculum_flow(self, base_state, executor):
        """Complete curriculum generation flow."""
        # Set up course
        executor.set_course_description(
            base_state,
            description="Learn Python",
            domain="Computer Science",
        )
        executor.set_course_length(base_state, duration_weeks=4, hours_per_week=10)
        executor.set_textbook(
            base_state,
            title="Python 101",
            authors=["Expert Author"],
        )

        # Create weeks and assignments
        for week_num in range(1, 3):
            executor.create_week(
                base_state,
                week_number=week_num,
                goal=f"Learn topic {week_num}",
                topics=[f"topic_{week_num}"],
            )
            executor.create_assignment(
                base_state,
                week_number=week_num,
                title=f"Assignment {week_num}",
                type="written",
                description=f"Complete assignment {week_num}",
            )
            executor.create_quiz(
                base_state,
                week_number=week_num,
                title=f"Quiz {week_num}",
                type="weekly",
                questions=[
                    {
                        "type": "multiple_choice",
                        "prompt": f"Question for week {week_num}",
                        "choices": ["A", "B", "C"],
                        "answer": "A",
                    }
                ],
            )

        # Verify completion
        result = executor.finish_course(base_state)
        assert result["status"] == "complete"
        assert base_state.course.status == CourseStatus.COMPLETE
        assert len(base_state.course.weeks) == 2
        assert all(len(w.assignments) > 0 for w in base_state.course.weeks)

    def test_week_without_quiz_allowed(self, base_state, executor):
        """Quiz is optional; week with only assignments is valid."""
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        executor.create_assignment(
            base_state, week_number=1, title="A", type="written", description="D"
        )
        # Don't create quiz
        result = executor.finish_course(base_state)
        assert result["status"] == "complete"

    def test_rich_assignment_creation(self, base_state, executor):
        """Assignment with all fields populated."""
        executor.create_week(base_state, week_number=1, goal="Goal", topics=["a"])
        result = executor.create_assignment(
            base_state,
            week_number=1,
            title="Comprehensive Project",
            type="project",
            description="Build a full-featured application",
            requirements=[
                "Use Python 3.11+",
                "Include unit tests",
                "Document with docstrings",
                "Follow PEP 8",
            ],
            resources=[
                {"title": "Python Docs", "url": "https://docs.python.org", "source": "web"},
                {"title": "Testing Guide", "url": "https://example.com/testing", "source": "article"},
            ],
            dueDate="2024-12-15",
            points=250,
            rubric="Code quality (50%), Tests (30%), Documentation (20%)",
        )
        assert result["status"] == "ok"
        assignment = base_state.course.weeks[0].assignments[0]
        assert len(assignment.requirements) == 4
        assert len(assignment.resources) == 2
        assert assignment.points == 250
