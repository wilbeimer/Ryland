import os
from uuid import UUID
from dotenv import load_dotenv
from anthropic import Anthropic

from backend.db import init_db
from agent.tools import TOOLS, ask_user, create_assignment, create_course, create_quiz, create_week

load_dotenv()

MAX_ITERATIONS = 10
MODEL = "claude-haiku-4-5"


class Agent():
    def __init__(self, user_id, client, model, tools=None, context_file=None):
        self.user_id = user_id
        self.client = client
        self.model = model
        self.tools = tools if tools is not None else []

        self.system_prompt = ''
        if context_file:
            with open(context_file, 'r') as context:
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
                return ask_user(tool_input)
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


def run_agent(user_id: UUID, task: str, **kwargs):
    messages: list[dict] = [{"role": "user", "content": task}]
    context_file = "agent/CONTEXT.md"
    agent = Agent(user_id=user_id, client=kwargs["client"], model=kwargs["model"], tools=TOOLS, context_file=context_file)

    for iteration in range(MAX_ITERATIONS):
        print(f"\n--- Turn {iteration + 1} ---")

        response = agent.make_call(messages)

        tool_results = []
        has_tool_use = False
        for block in response.content:
            if block.type == "text":
                print(f"Claude: {block.text}")
            elif block.type == "tool_use":
                has_tool_use = True
                print(f"Using tool: {block.name}")
                print(f"Input: {block.input}")

                # Execute the tool
                result, is_error = agent.process_tool_call(block.name, block.input)
                print(f"Result: {result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                    "is_error": is_error
                })

        messages.append({"role": "assistant", "content": response.content})

        if not has_tool_use:
            print("Agent complete")
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})


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
