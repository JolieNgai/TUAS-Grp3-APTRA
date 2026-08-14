import openai
from flask import current_app


class LLMService:
    @staticmethod
    def _normalize_tone(tone: str) -> str:
        tone_map = {
            "professional": "professional and polished",
            "casual": "casual and conversational",
            "friendly": "friendly and warm",
            "formal": "formal and respectful",
            "diplomatic": "diplomatic and tactful",
        }
        return tone_map.get((tone or "").strip().lower(), "professional and polished")

    @staticmethod
    def _get_max_tokens(length: str) -> int:
        token_map = {"short": 25, "medium": 50, "long": 250}
        return token_map.get((length or "").strip().lower(), 50)

    @staticmethod
    def build_reply_prompt(email_text: str, tone: str, length: str) -> str:
        tone = LLMService._normalize_tone(tone)
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
            from groq import Groq

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

    def generate_response(
        self, email_text: str, tone: str = "professional", length: str = "medium"
    ) -> str:
        prompt = self.build_reply_prompt(email_text, tone, length)
        messages = [
            {
                "role": "system",
                "content": "You are an expert email assistant who drafts ready-to-send replies.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=min(
                self._get_max_tokens(length), current_app.config.get("MAX_TOKENS", 500)
            ),
            temperature=current_app.config["TEMPERATURE"],
        )

        content = response.choices[0].message.content
        return content.strip() if content else ""
