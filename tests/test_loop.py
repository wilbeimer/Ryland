"""
Tests for backend.ai.curriculum_agent.loop.generate_curriculum.

These tests never touch the real Groq/OpenAI-style client or the real
execute_tool implementation — both are patched out. That's deliberate:
this loop is a state machine wrapped around two side-effecting
collaborators (the LLM client and the tool executor), so the thing worth
testing is the control flow — when it stops, when it nudges, when it
gives up — not any particular model's behavior.

Adjust the two `MODULE` / patch-target strings below if the real file
lives at a different import path than backend.ai.curriculum_agent.loop.
"""

import enum
import json
from unittest.mock import MagicMock, patch

import pytest

from backend.ai.curriculum_agent.loop import generate_curriculum, MODEL

MODULE = "backend.ai.curriculum_agent.loop"


# --------------------------------------------------------------------------
# Fakes standing in for the real RylandState / OpenAI-style response objects.
# Kept dependency-free on purpose so these tests don't rely on the actual
# pydantic models matching this shape exactly — only the attributes the
# loop itself touches (request.name/description, course.status, errors).
# --------------------------------------------------------------------------


class CourseStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class FakeRequest:
    def __init__(self, name="Intro to Testing", description="A course about testing"):
        self.name = name
        self.description = description


class FakeCourse:
    def __init__(self, status=CourseStatus.IN_PROGRESS):
        self.status = status


class FakeState:
    def __init__(self, status=CourseStatus.IN_PROGRESS):
        self.request = FakeRequest()
        self.course = FakeCourse(status)
        self.errors = []


class FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        # Mirrors the real API: arguments arrive as a JSON string.
        self.arguments = (
            arguments if isinstance(arguments, str) else json.dumps(arguments)
        )


class FakeToolCall:
    def __init__(self, name, arguments, call_id=None):
        self.id = call_id or f"call_{name}"
        self.function = FakeFunction(name, arguments)


class FakeMessage:
    """Stand-in for response.choices[0].message."""

    def __init__(self, tool_calls=None, content=None):
        self.tool_calls = tool_calls or None
        self.content = content

    def model_dump(self, exclude_none=True):
        dump = {"role": "assistant"}
        if self.content is not None or not exclude_none:
            dump["content"] = self.content
        if self.tool_calls:
            dump["tool_calls"] = [
                {
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in self.tool_calls
            ]
        return dump


def make_response(tool_calls=None, content=None):
    message = FakeMessage(tool_calls=tool_calls, content=content)
    choice = MagicMock(message=message)
    return MagicMock(choices=[choice])


@pytest.fixture
def mock_client():
    """A MagicMock client whose chat.completions.create() is scripted per-test."""
    client = MagicMock()
    with patch(f"{MODULE}.get_client", return_value=client):
        yield client


# --------------------------------------------------------------------------
# Happy path
# --------------------------------------------------------------------------


def test_returns_immediately_when_finish_course_reports_complete(mock_client):
    finish_call = FakeToolCall("finish_course", {})
    mock_client.chat.completions.create.return_value = make_response(
        tool_calls=[finish_call]
    )
    state = FakeState()

    with patch(
        f"{MODULE}.execute_tool", return_value={"status": "complete"}
    ) as exec_mock:
        result = generate_curriculum(state)

    assert result is state
    assert state.errors == []
    exec_mock.assert_called_once_with("finish_course", {}, state)
    # Only one round-trip to the model was needed.
    mock_client.chat.completions.create.assert_called_once()


def test_multiple_tool_calls_in_one_message_are_all_executed(mock_client):
    calls = [
        FakeToolCall("set_course_description", {"description": "x"}, call_id="a"),
        FakeToolCall("set_course_length", {"weeks": 4}, call_id="b"),
    ]
    finish = FakeToolCall("finish_course", {}, call_id="c")
    mock_client.chat.completions.create.side_effect = [
        make_response(tool_calls=calls),
        make_response(tool_calls=[finish]),
    ]
    state = FakeState()

    with patch(f"{MODULE}.execute_tool", return_value={"status": "ok"}) as exec_mock:
        # Make the finish_course call (third invocation) report complete.
        exec_mock.side_effect = [
            {"status": "ok"},
            {"status": "ok"},
            {"status": "complete"},
        ]
        result = generate_curriculum(state)

    assert result is state
    assert exec_mock.call_count == 3
    exec_mock.assert_any_call("set_course_description", {"description": "x"}, state)
    exec_mock.assert_any_call("set_course_length", {"weeks": 4}, state)


# --------------------------------------------------------------------------
# Error handling within a single tool call
# --------------------------------------------------------------------------


def test_malformed_tool_arguments_are_reported_without_calling_execute_tool(
    mock_client,
):
    bad_call = FakeToolCall("create_week", "{not valid json", call_id="bad")
    finish = FakeToolCall("finish_course", {})
    mock_client.chat.completions.create.side_effect = [
        make_response(tool_calls=[bad_call]),
        make_response(tool_calls=[finish]),
    ]
    state = FakeState()

    with patch(f"{MODULE}.execute_tool") as exec_mock:
        exec_mock.return_value = {"status": "complete"}
        generate_curriculum(state)

    # execute_tool must never see the unparsable call.
    for c in exec_mock.call_args_list:
        assert c.args[0] != "create_week" or c.args[0] == "finish_course"
    exec_mock.assert_called_once_with("finish_course", {}, state)


def test_tool_execution_error_does_not_crash_the_loop(mock_client):
    failing_call = FakeToolCall("create_assignment", {})
    finish = FakeToolCall("finish_course", {})
    mock_client.chat.completions.create.side_effect = [
        make_response(tool_calls=[failing_call]),
        make_response(tool_calls=[finish]),
    ]
    state = FakeState()

    with patch(f"{MODULE}.execute_tool") as exec_mock:
        exec_mock.side_effect = [
            {"error": "week 1 does not exist"},
            {"status": "complete"},
        ]
        result = generate_curriculum(state)

    assert result is state
    assert mock_client.chat.completions.create.call_count == 2


def test_finish_course_with_incomplete_status_keeps_the_loop_going(mock_client):
    finish_incomplete = FakeToolCall("finish_course", {})
    finish_complete = FakeToolCall("finish_course", {})
    mock_client.chat.completions.create.side_effect = [
        make_response(tool_calls=[finish_incomplete]),
        make_response(tool_calls=[finish_complete]),
    ]
    state = FakeState()

    with patch(f"{MODULE}.execute_tool") as exec_mock:
        exec_mock.side_effect = [
            {"status": "incomplete", "missing": ["week 2 has no assignment"]},
            {"status": "complete"},
        ]
        result = generate_curriculum(state)

    assert result is state
    assert exec_mock.call_count == 2
    assert mock_client.chat.completions.create.call_count == 2


# --------------------------------------------------------------------------
# No tool_calls in the model's message
# --------------------------------------------------------------------------


def test_no_tool_calls_and_incomplete_course_gets_nudged_and_continues(mock_client):
    finish = FakeToolCall("finish_course", {})
    mock_client.chat.completions.create.side_effect = [
        make_response(tool_calls=None, content="Let me think about this."),
        make_response(tool_calls=[finish]),
    ]
    state = FakeState(status=CourseStatus.IN_PROGRESS)

    with patch(f"{MODULE}.execute_tool", return_value={"status": "complete"}):
        result = generate_curriculum(state)

    assert result is state
    assert mock_client.chat.completions.create.call_count == 2
    # A nudge message should have been injected before the second call.
    second_call_messages = mock_client.chat.completions.create.call_args_list[1].kwargs[
        "messages"
    ]
    assert any(
        m.get("role") == "user"
        and "stopped without calling finish_course" in m.get("content", "")
        for m in second_call_messages
    )


def test_no_tool_calls_and_complete_course_returns_cleanly(mock_client):
    """
    If the model stops calling tools while state.course.status is already
    COMPLETE, that's a successful finish (finish_course must have set that
    status on an earlier iteration) — the loop should return immediately
    without recording a max_iterations error.
    """
    mock_client.chat.completions.create.return_value = make_response(
        tool_calls=None, content="Done!"
    )
    state = FakeState(status=CourseStatus.COMPLETE)

    result = generate_curriculum(state, max_iterations=5)

    assert result is state
    mock_client.chat.completions.create.assert_called_once()
    assert state.errors == []


# --------------------------------------------------------------------------
# max_iterations exhaustion
# --------------------------------------------------------------------------


def test_gives_up_after_max_iterations_without_finish_course(mock_client):
    stall_call = FakeToolCall("create_week", {"number": 1})
    mock_client.chat.completions.create.return_value = make_response(
        tool_calls=[stall_call]
    )
    state = FakeState()

    with patch(f"{MODULE}.execute_tool", return_value={"status": "ok"}):
        result = generate_curriculum(state, max_iterations=3)

    assert result is state
    assert mock_client.chat.completions.create.call_count == 3
    assert len(state.errors) == 1
    assert "Hit max_iterations (3)" in state.errors[0]


# --------------------------------------------------------------------------
# Request construction / parameter plumbing
# --------------------------------------------------------------------------


def test_system_and_user_messages_are_built_from_state(mock_client):
    finish = FakeToolCall("finish_course", {})
    mock_client.chat.completions.create.return_value = make_response(
        tool_calls=[finish]
    )
    state = FakeState()
    state.request.name = "German for Beginners"
    state.request.description = "Six weeks of A1 grammar and vocabulary."

    with patch(f"{MODULE}.execute_tool", return_value={"status": "complete"}):
        generate_curriculum(state)

    sent_messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    assert sent_messages[0]["role"] == "system"
    assert "Ryland" in sent_messages[0]["content"]
    assert sent_messages[1]["role"] == "user"
    assert "German for Beginners" in sent_messages[1]["content"]
    assert "Six weeks of A1 grammar and vocabulary." in sent_messages[1]["content"]


def test_client_is_called_with_expected_default_params(mock_client):
    finish = FakeToolCall("finish_course", {})
    mock_client.chat.completions.create.return_value = make_response(
        tool_calls=[finish]
    )
    state = FakeState()

    with patch(f"{MODULE}.execute_tool", return_value={"status": "complete"}), patch(
        f"{MODULE}.TOOLS", ["sentinel-tool-schema"]
    ):
        generate_curriculum(state)

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == MODEL
    assert kwargs["tools"] == ["sentinel-tool-schema"]
    assert kwargs["tool_choice"] == "auto"
    assert kwargs["max_tokens"] == 4000


def test_custom_model_is_forwarded_to_the_client(mock_client):
    finish = FakeToolCall("finish_course", {})
    mock_client.chat.completions.create.return_value = make_response(
        tool_calls=[finish]
    )
    state = FakeState()

    with patch(f"{MODULE}.execute_tool", return_value={"status": "complete"}):
        generate_curriculum(state, model="llama-3.1-8b-instant")

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "llama-3.1-8b-instant"


def test_tool_call_id_is_preserved_in_the_tool_result_message(mock_client):
    week_call = FakeToolCall("create_week", {"number": 1}, call_id="call_xyz789")
    finish = FakeToolCall("finish_course", {}, call_id="call_finish")
    mock_client.chat.completions.create.side_effect = [
        make_response(tool_calls=[week_call]),
        make_response(tool_calls=[finish]),
    ]
    state = FakeState()

    with patch(f"{MODULE}.execute_tool") as exec_mock:
        exec_mock.side_effect = [{"status": "ok"}, {"status": "complete"}]
        generate_curriculum(state)

    # `messages` is one list mutated in place across iterations, so
    # call_args_list holds references, not snapshots — inspect the final
    # state and check the first tool result landed with the right id,
    # before the finish_course result that follows it.
    final_messages = mock_client.chat.completions.create.call_args_list[-1].kwargs[
        "messages"
    ]
    tool_messages = [m for m in final_messages if m.get("role") == "tool"]
    assert [m["tool_call_id"] for m in tool_messages] == ["call_xyz789", "call_finish"]
    assert json.loads(tool_messages[0]["content"]) == {"status": "ok"}
