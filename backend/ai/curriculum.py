from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)


def test_ai_response() -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": "Introduce yourself to the user"
            }
        ]
    )

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("No response from AI")
    return json.loads(content)


def generate_course_description(course_name: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert curriculum designer. Return only JSON, no markdown, no explanation."
            },
            {
                "role": "user",
                "content": f"""Given the course name '{course_name}', generate:
    1. A detailed description of the course
    2. The academic domain it belongs to (e.g. Computer Science, Mathematics, History)
    3. Any subdomains or topics it covers
    4. prerequisites a student should have before taking this course

    Return as JSON in this exact format:
    {{
        "description": "...",
        "domain": "...",
        "subdomains": ["...", "..."],
        "prerequisites": ["...", "..."]
    }}"""
            }
        ]
    )

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("No response from AI")
    return json.loads(content)


if __name__ == "__main__":
    print(generate_course_description("Machine Learning"))
