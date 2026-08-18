import re

from flask import current_app
from groq import Groq


class LLMService:
    _OUTPUT_MARKER = re.compile(
        r"(?is)(?:\[\s*output generation\s*\]|\bfinal (?:output generation|answer|email|reply))"
        r"(?:\*\*)?\s*:?\s*(?:\*\*)?\s*(?:-+>)?\s*(.*)$"
    )
    _DRAFT_SECTION = re.compile(
        r"(?is)(?:\*\*)?draft(?:\s*-\s*mental refinement)?(?:\*\*)?\s*:?\s*(?:\*\*)?\s*(.*?)"
        r"(?=\n\s*(?:check constraints|\d+\.\s*\*\*final output generation))"
    )

    @staticmethod
    def build_reply_prompt(email_text: str, tone: str, length: str, additional_context: str = "") -> str:
        tone = (tone or "professional").strip().lower()
        length = (length or "medium").strip().lower()

        length_guidance = {
            "short": "Keep the reply concise, ideally 1-2 sentences.",
            "medium": "Keep the reply clear and balanced, around 3-5 sentences.",
            "long": "Write a fuller response with more detail, around 6 or more sentences.",
        }.get(length, "Keep the reply clear and professional.")

        context_instruction = ""
        if additional_context.strip():
            context_instruction = f"Additional context/instructions from the user:\n{additional_context.strip()}\n\n"

        return (
            "Write a reply email based on the received email below. "
            "Use a {tone} tone and adapt the message to the requested email length. "
            "Return only the final email reply text, with no explanations or notes.\n\n"
            "Email to respond to:\n{email}\n\n"
            "{context_instruction}\n"
            "Tone: {tone}\n"
            "Requested length: {length}\n"
            "Length guidance: {length_guidance}\n"
        ).format(
            tone=tone,
            length=length,
            email=email_text.strip(),
            length_guidance=length_guidance,
            context_instruction=context_instruction,
        )

    def __init__(self):
        api_key = current_app.config.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")
        self.client = Groq(api_key=api_key)
        self.model = current_app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    def generate_response(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "Draft the requested email reply. Return only the text the sender "
                    "should send. Never include analysis, reasoning, checklists, labels, "
                    "quotes around the reply, or commentary about the result."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        request_options = dict(
            model=self.model,
            messages=messages,
            max_tokens=current_app.config["MAX_TOKENS"],
            temperature=current_app.config["TEMPERATURE"],
        )
        if self.model.startswith("qwen/qwen3"):
            # Email drafting does not need chain-of-thought. Qwen otherwise uses
            # the completion budget for reasoning and can expose it as content.
            request_options.update(reasoning_effort="none", reasoning_format="hidden")

        response = self.client.chat.completions.create(**request_options)

        return self.clean_generated_reply(response.choices[0].message.content)

    @classmethod
    def clean_generated_reply(cls, content: str) -> str:
        """Remove reasoning wrappers occasionally emitted by reasoning-capable models."""
        cleaned = (content or "").strip()
        cleaned = re.sub(r"(?is)<think>.*?</think>", "", cleaned).strip()

        draft_match = cls._DRAFT_SECTION.search(cleaned)
        marker_match = cls._OUTPUT_MARKER.search(cleaned)
        if marker_match:
            final_section = marker_match.group(1).strip()
            if final_section and not final_section.lower().startswith("(ensure"):
                cleaned = final_section
            elif draft_match:
                # Recover the completed draft if the model exhausted its token
                # budget immediately before emitting the labelled final answer.
                cleaned = draft_match.group(1).strip()

        # Some models wrap the final reply in quotes after an output marker.
        if len(cleaned) >= 2 and cleaned[0] in {'"', "'"}:
            closing_quote = cleaned.rfind(cleaned[0])
            if closing_quote > 0:
                cleaned = cleaned[1:closing_quote].strip()

        return cleaned

