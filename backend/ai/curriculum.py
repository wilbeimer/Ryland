from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


def test_ai_response() -> str:
    response = client.responses.create(
        input="Explain the importance of fast language models",
        model="openai/gpt-oss-20b",
    )

    return response.output_text
