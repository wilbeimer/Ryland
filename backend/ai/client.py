from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()


def get_client():
    return Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
