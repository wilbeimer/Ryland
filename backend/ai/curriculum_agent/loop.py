"""
Agentic curriculum generation loop.

Replaces the fixed 01-07 stage pipeline in run.py: instead of a hardcoded
sequence of AI calls each mapped to one apply_* function, the model decides
what to call and when, driven entirely by the tool descriptions in
tool_schemas.py. Adding/removing/changing what gets generated per assignment
is now a prompt/schema change, not a pipeline change.
"""

import json

from backend.models import RylandState
from backend.ai.client import get_client
from backend.ai.curriculum_agent.tool_schemas import TOOLS
from backend.ai.curriculum_agent.executor import execute_tool

SYSTEM_PROMPT = """You are Ryland, an expert curriculum designer. Build a complete, \
well-sequenced course by calling the provided tools. Rules:

1. Call set_course_description and set_course_length before creating any weeks.
2. Create weeks in order, starting at week 1, using create_week.
3. For each week, create at least one assignment with create_assignment. Assignments \
must be fully specified in a single call: description, requirements, rubric, points, \
and any resources all go in that one call. There is no separate "add details" step.
4. Use search_youtube when a video resource would genuinely help. Then attach the \
chosen result to an assignment's resources with source='youtube', using only its \
title and url (the search result has extra fields Resource doesn't accept).
5. Add a quiz per week where it makes sense with create_quiz.
6. Call finish_course only once every week has at least one assignment. If it \
returns an error, it lists what's missing — keep working and call it again once \
the course is actually complete.
7. If any tool call returns an error, read it, fix your arguments, and try again. \
Don't repeat the same failing call unchanged.
"""

MODEL = "llama-3.3-70b-versatile"
MAX_ITERATIONS = 60


def generate_curriculum(
    state: RylandState,
    model: str = MODEL,
    max_iterations: int = MAX_ITERATIONS,
) -> RylandState:
    client = get_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Generate a complete curriculum for:\n"
                f"Name: {state.request.name}\n"
                f"Description: {state.request.description}"
            ),
        },
    ]

    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=4000,
        )
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            # Model stopped talking without calling finish_course. Nudge once
            # rather than silently accepting an incomplete course.
            if state.course.status != state.course.status.COMPLETE:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You stopped without calling finish_course. If the course "
                            "is done, call finish_course now. Otherwise keep going."
                        ),
                    }
                )
                continue
            break

        for tool_call in message.tool_calls:
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                result = {"error": f"Could not parse arguments as JSON: {e}"}
            else:
                result = execute_tool(tool_call.function.name, args, state)

            print(
                f"[{iteration}] {tool_call.function.name}({tool_call.function.arguments}) -> {result}"
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

            if (
                tool_call.function.name == "finish_course"
                and result.get("status") == "complete"
            ):
                return state

    state.errors.append(
        f"Hit max_iterations ({max_iterations}) without calling finish_course successfully."
    )
    return state
