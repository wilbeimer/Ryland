import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from anthropic import Anthropic
from dotenv import load_dotenv

from agent.tools import (
    TOOLS,
    ask_user,
    create_assignment,
    create_course,
    create_quiz,
    create_week,
)
from backend.db import init_db

load_dotenv()

MAX_ITERATIONS = 10
MODEL = "claude-haiku-4-5"
CONTEXT_FILE = Path(__file__).resolve().parent / "CONTEXT.md"


@dataclass
class AgentRunResult:
    course_id: str | None
    summary: str
    completed: bool


class Agent:
    def __init__(self, user_id, client, model, tools=None, context_file=None, ask=None):
        self.user_id = user_id
        self.client = client
        self.model = model
        self.tools = tools if tools is not None else []
        self.ask = ask if ask is not None else ask_user

        self.system_prompt = ""
        if context_file:
            with open(context_file, "r") as context:
                self.system_prompt = context.read()

        self.responses = []

    def process_tool_call(self, tool_name: str, tool_input: dict):
        match tool_name:
            case "create_course":
                return create_course(tool_input, self.user_id)
            case "create_week":
                return create_week(tool_input)
            case "create_assignment":
                return create_assignment(tool_input)
            case "create_quiz":
                return create_quiz(tool_input)
            case "ask_user":
                return self.ask(tool_input)
            case _:
                return f"Unknown tool: {tool_name}", True

    def make_call(self, messages):
        if type(self.client) is Anthropic:
            message = self.client.messages.create(
                max_tokens=1024,
                messages=messages,
                tools=self.tools,
                model=self.model,
                system=self.system_prompt,
            )
        else:
            raise ValueError("Model couldn't be matched to client")

        self.responses.append(message)
        return self.responses[-1]


def run_agent(user_id: UUID, task: str, **kwargs) -> AgentRunResult:
    messages: list[dict] = [{"role": "user", "content": task}]
    on_progress: Callable[[str], None] | None = kwargs.get("on_progress")
    agent = Agent(
        user_id=user_id,
        client=kwargs["client"],
        model=kwargs["model"],
        tools=TOOLS,
        context_file=CONTEXT_FILE,
        ask=kwargs.get("ask"),
    )

    course_id = None
    summary_parts: list[str] = []
    completed = False

    for iteration in range(MAX_ITERATIONS):
        print(f"\n--- Turn {iteration + 1} ---")
        if on_progress:
            on_progress(f"Turn {iteration + 1}")

        response = agent.make_call(messages)

        tool_results = []
        has_tool_use = False
        for block in response.content:
            if block.type == "text":
                print(f"Claude: {block.text}")
                if block.text and block.text.strip():
                    summary_parts.append(block.text.strip())
            elif block.type == "tool_use":
                has_tool_use = True
                print(f"Using tool: {block.name}")
                print(f"Input: {block.input}")
                if on_progress:
                    on_progress(f"Using {block.name}")

                # Execute the tool
                result, is_error = agent.process_tool_call(block.name, block.input)
                print(f"Result: {result}")

                if (
                    block.name == "create_course"
                    and not is_error
                    and isinstance(result, dict)
                    and result.get("course_id")
                    and course_id is None
                ):
                    course_id = str(result["course_id"])

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                        "is_error": is_error,
                    }
                )

        messages.append({"role": "assistant", "content": response.content})

        if not has_tool_use:
            print("Agent complete")
            completed = True
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    summary = "\n".join(summary_parts)
    return AgentRunResult(course_id=course_id, summary=summary, completed=completed)


def learner_brief(
    goal: str, level: str, time_available: str, timezone_name: str
) -> str:
    """The facts CONTEXT.md would otherwise collect with ask_user."""
    try:
        now = datetime.now(ZoneInfo(timezone_name))
        clock = now.isoformat(timespec="minutes")
    except (ZoneInfoNotFoundError, ValueError):
        now = datetime.now(UTC)
        clock = (
            f"{now.isoformat(timespec='minutes')} "
            f"(could not resolve timezone {timezone_name}; use that name for due-date offsets)"
        )

    return (
        f"Goal: {goal}\n"
        f"Level: {level}\n"
        f"Time available: {time_available}\n"
        f"Timezone: {timezone_name}\n"
        f"Current date and time: {clock}\n"
    )


def run_generation(
    *,
    user_id: UUID,
    goal: str,
    level: str,
    time_available: str,
    timezone_name: str,
    on_progress: Callable[[str], None] | None = None,
) -> AgentRunResult:
    """Run one course build without reading from the terminal.

    The brief is what the CLI collects through ask_user: goal, level, time
    available, timezone, and the current date. If the model calls ask_user
    anyway, the tool answers from that same brief.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    brief = learner_brief(goal, level, time_available, timezone_name)
    task = (
        "Build a complete course for this learner. "
        "The brief already includes their goal, level, time available, timezone, "
        "and the current date. Start creating the course. "
        "Do not call ask_user for information that is in the brief.\n\n"
        f"{brief}"
    )

    def answer_from_brief(tool_input: dict) -> tuple[str, bool]:
        question = ""
        if isinstance(tool_input, dict):
            question = str(tool_input.get("question") or "")
        prefix = "That information was already provided. Continue building from this brief.\n"
        if question:
            prefix += f"Question: {question}\n"
        return prefix + brief, False

    client = Anthropic(api_key=api_key)
    return run_agent(
        user_id=user_id,
        task=task,
        model=MODEL,
        client=client,
        ask=answer_from_brief,
        on_progress=on_progress,
    )


def main(user_id: UUID | None = None):
    if not user_id:
        user_id = UUID("00000000-0000-0000-0000-000000000001")

    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    task = input("> ")
    run_agent(user_id=user_id, task=task, model=MODEL, client=client)


if __name__ == "__main__":
    init_db()
    main()
