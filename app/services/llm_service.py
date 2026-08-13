import openai
from flask import current_app


class LLMService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=current_app.config["OPENAI_API_KEY"])

    def generate_response(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=current_app.config["OPENAI_MODEL"],
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=current_app.config["OPENAI_MAX_TOKENS"],
            temperature=current_app.config["OPENAI_TEMPERATURE"],
        )

        return response.choices[0].message.content.strip()
