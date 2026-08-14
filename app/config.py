import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    OPENAI_MAX_TOKENS = int(os.getenv("MAX_TOKENS", "500"))
    OPENAI_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
