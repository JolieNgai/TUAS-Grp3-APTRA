import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in .env and cannot be empty.")
    
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    if LLM_PROVIDER == "groq" and not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
    
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "500"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

