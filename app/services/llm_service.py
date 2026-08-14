import openai
from flask import current_app
from groq import Groq


class LLMService:
    @staticmethod
    def build_reply_prompt(email_text: str, tone: str, length: str) -> str:
        tone = (tone or "professional").strip().lower()
        length = (length or "medium").strip().lower()

        length_guidance = {
            "short": "Keep the reply concise, ideally 1-2 sentences.",
            "medium": "Keep the reply clear and balanced, around 3-5 sentences.",
            "long": "Write a fuller response with more detail, around 6 or more sentences.",
        }.get(length, "Keep the reply clear and professional.")

        return (
            "Write a reply email based on the received email below. "
            "Use a {tone} tone and adapt the message to the requested email length. "
            "Return only the final email reply text, with no explanations or notes.\n\n"
            "Email to respond to:\n{email}\n\n"
            "Tone: {tone}\n"
            "Requested length: {length}\n"
            "Length guidance: {length_guidance}\n"
        ).format(
            tone=tone,
            length=length,
            email=email_text.strip(),
            length_guidance=length_guidance,
        )

    def __init__(self):
        provider = current_app.config.get("LLM_PROVIDER", "groq").lower()

        if provider == "groq":
            api_key = current_app.config.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY is not configured.")
            self.client = Groq(api_key=api_key)
            self.model = current_app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")
            self.provider = "groq"
            return

        api_key = current_app.config.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = current_app.config.get("OPENAI_MODEL", "gpt-4o-mini")
        self.provider = "openai"

    def generate_response(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": "You are a helpful assistant that drafts email replies."},
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=current_app.config["MAX_TOKENS"],
            temperature=current_app.config["TEMPERATURE"],
        )

        return response.choices[0].message.content.strip()

