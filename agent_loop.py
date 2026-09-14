import os
from dotenv import load_dotenv
from anthropic import Anthropic

from backend.db import create_course
from backend.models import Course

load_dotenv()

TOOLS = [
    {
        "name": "create_course",
        "description": "Creates a new course and adds it to the database",
        "input_schema": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "The name of the course"
                },
                "course_description": {
                    "type": "string",
                    "description": "A detailed description of the course"
                }
            },
            "required": ["course_name", "course_description"]
        }
    }
]


class Agent():
    def __init__(self, client, model, tools=None):
        self.client = client
        self.model = model
        self.tools = tools if tools is not None else []

        self.responses = []

    def process_tool_call(self, tool_name: str, tool_input: dict):
        if tool_name == "create_course":
            course = Course(
                name=tool_input["course_name"],
                desc=tool_input["course_description"]
            )
            return create_course(
                course=course
            )
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def make_call(self, messages):
        if type(self.client) is Anthropic:
            message = self.client.messages.create(
                max_tokens=1024,
                messages=messages,
                tools=self.tools,
                model=self.model
            )
        else:
            raise ValueError("Model couldn't be matched to client")

        self.responses.append(message)
        return self.responses[-1]


def run_agent(task: str, **kwargs):
    messages: list[dict] = [{"role": "user", "content": task}]
    agent = Agent(kwargs["client"], kwargs["model"], tools=TOOLS)

    for iteration in range(5):
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
                result = agent.process_tool_call(block.name, block.input)
                print(f"Result: {result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result)
                })

        messages.append({"role": "assistant", "content": response.content})

        if not has_tool_use:
            print("Agent complete")
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})


def main():
    MODEL = "claude-haiku-4-5"
    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    task = input(": ")
    run_agent(task, model=MODEL, client=client)


if __name__ == "__main__":
    main()
