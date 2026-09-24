import os
from dotenv import load_dotenv
from anthropic import Anthropic

from backend.db import InvalidCourseError, create_course, init_db
from backend.models import Course
from agent.tools import TOOLS

load_dotenv()


class Agent():
    def __init__(self, client, model, tools=None, context_file=None):
        self.client = client
        self.model = model
        self.tools = tools if tools is not None else []

        self.system_prompt = ''
        if context_file:
            with open(context_file, 'r') as context:
                self.system_prompt = context.read()

        self.responses = []

    def process_tool_call(self, tool_name: str, tool_input: dict):
        if tool_name == "create_course":
            try:
                course = Course(
                    name=tool_input["course_name"],
                    desc=tool_input["course_description"]
                )
                course_id = create_course(course=course)
                return {"course_id": course_id}, False
            except InvalidCourseError as e:
                return {"content": str(e)}, True
            except KeyError as e:
                return {"content": f"Missing required fields {e}"}, True
        elif tool_name == "ask_user":
            answer = input(f"\n{tool_input['question']}\n> ")
            return answer, False
        else:
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


def run_agent(task: str, **kwargs):
    messages: list[dict] = [{"role": "user", "content": task}]
    context_file = "agent/CONTEXT.md"
    agent = Agent(kwargs["client"], kwargs["model"], tools=TOOLS, context_file=context_file)

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


def main():
    MODEL = "claude-haiku-4-5"
    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    task = input(": ")
    run_agent(task, model=MODEL, client=client)


if __name__ == "__main__":
    init_db()
    main()
