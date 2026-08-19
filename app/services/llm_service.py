import re

from flask import current_app
from groq import Groq


class LLMService:
    _PLACEHOLDER_ALIASES = (
        (re.compile(r"\[(?:enter\s+)?passport(?:_number|\s+number)?\]", re.IGNORECASE), "[enter passport number]"),
        (re.compile(r"\[(?:enter\s+)?(?:nric(?:_or_?|\s+or\s+)?fin|nric|fin)\]", re.IGNORECASE), "[enter NRIC or FIN]"),
        (re.compile(r"\[(?:enter\s+)?(?:phone|mobile)(?:_number|\s+number)?\]", re.IGNORECASE), "[enter phone number]"),
        (re.compile(r"\[(?:enter\s+)?credit_?card(?:_number|\s+number)?\]", re.IGNORECASE), "[enter credit card number]"),
        (re.compile(r"\[(?:enter\s+)?(?:payment_?card|card)(?:_number|\s+number)?\]", re.IGNORECASE), "[enter payment card number]"),
    )
    _SINGAPORE_ID = re.compile(r"\b[STFGM]\d{7}[A-Z]\b", re.IGNORECASE)
    _PASSPORT = re.compile(
        r"(?i:\bpassport(?:\s*(?:number|no\.?|#))?\s*(?:is|:|=)?\s*)"
        r"[A-Z0-9]{6,20}\b"
    )
    _LABELLED_PHONE = re.compile(
        r"(?i:\b(?:phone|mobile|tel(?:ephone)?)\s*(?:number|no\.?|#)?\s*(?:is|:|=)?\s*)"
        r"(?:\+?\d[\d\s().-]{6,}\d)"
    )
    _INTERNATIONAL_PHONE = re.compile(r"(?<!\w)\+\d[\d\s().-]{6,}\d(?!\w)")
    _SINGAPORE_PHONE = re.compile(r"(?<!\d)[689]\d{7}(?!\d)")
    _LABELLED_CARD = re.compile(
        r"(?i:\b(?P<kind>credit|payment|debit)\s*card\s*(?:number|no\.?|#)?\s*(?:is|:|=)?\s*)"
        r"(?P<number>(?:\d[ -]?){12,18}\d)"
    )
    _PAYMENT_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
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
        email_text = LLMService.mask_private_information(email_text)
        additional_context = LLMService.mask_private_information(additional_context)

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
            "Return only the final email reply text, with no explanations or notes. "
            "Write the reply normally and answer the email's request. Whenever the reply "
            "needs protected information, use its exact placeholder: [enter credit card number], "
            "[enter passport number], [enter NRIC or FIN], [enter phone number], or "
            "[enter payment card number]. These placeholders contain no real private data, "
            "Never omit a necessary placeholder, invent a value, or restore a masked value.\n\n"
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
        self.model = current_app.config.get("GROQ_MODEL", "qwen/qwen3.6-27b")

    def generate_response(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "Draft the requested email reply. Return only the text the sender "
                    "should send. Never include analysis, reasoning, checklists, labels, "
                    "quotes around the reply, or commentary about the result. Preserve "
                    "the exact privacy placeholder whenever protected information is "
                    "needed in the reply: [enter credit card number], [enter passport number], "
                    "[enter NRIC or FIN], [enter phone number], or [enter payment card number]. "
                    "The placeholders are safe template text, so do not refuse to include them. Never guess "
                    "the private values they replace."
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

        cleaned_reply = self.clean_generated_reply(response.choices[0].message.content)
        masked_reply = self.mask_private_information(cleaned_reply)
        return self.ensure_required_placeholders(masked_reply, prompt)

    @classmethod
    def mask_private_information(cls, content: str) -> str:
        """Mask common high-risk identifiers before API processing or display."""
        masked = content or ""
        for pattern, replacement in cls._PLACEHOLDER_ALIASES:
            masked = pattern.sub(replacement, masked)
        masked = cls._SINGAPORE_ID.sub("[enter NRIC or FIN]", masked)
        masked = cls._PASSPORT.sub("passport number [enter passport number]", masked)
        masked = cls._LABELLED_PHONE.sub("phone number [enter phone number]", masked)
        masked = cls._INTERNATIONAL_PHONE.sub("[enter phone number]", masked)
        masked = cls._SINGAPORE_PHONE.sub("[enter phone number]", masked)

        def mask_labelled_card(match):
            kind = match.group("kind").lower()
            placeholder = (
                "[enter credit card number]" if kind == "credit"
                else "[enter payment card number]"
            )
            return f"{kind} card number {placeholder}"

        masked = cls._LABELLED_CARD.sub(mask_labelled_card, masked)

        def mask_valid_card(match):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 19 and cls._passes_luhn_check(digits):
                return "[enter payment card number]"
            return match.group(0)

        return cls._PAYMENT_CARD.sub(mask_valid_card, masked)

    @classmethod
    def ensure_required_placeholders(cls, reply: str, prompt: str) -> str:
        """Ensure protected fields requested by the email remain editable in the reply."""
        supported = (
            "[enter credit card number]",
            "[enter passport number]",
            "[enter NRIC or FIN]",
            "[enter phone number]",
            "[enter payment card number]",
        )
        # The prompt instructions mention every supported placeholder. Inspect
        # only the user-supplied email/context section so unrelated placeholders
        # are never added to the generated reply.
        user_content = prompt
        email_marker = "Email to respond to:\n"
        if email_marker in prompt:
            user_content = prompt.split(email_marker, 1)[1]
            if "\nTone:" in user_content:
                user_content = user_content.rsplit("\nTone:", 1)[0]

        required = [item for item in supported if item in user_content]
        missing = [item for item in required if item not in reply]
        if not missing:
            return reply

        refusal = re.search(
            r"(?i)\b(?:cannot|can't|unable to|won't)\s+(?:provide|share|repeat)|security reasons",
            reply,
        )
        fields = ", ".join(missing)
        if refusal:
            return f"Thank you for your message. {fields}."
        return f"{reply.rstrip()}\n\n{fields}".strip()

    @staticmethod
    def _passes_luhn_check(digits: str) -> bool:
        total = 0
        parity = len(digits) % 2
        for index, character in enumerate(digits):
            value = int(character)
            if index % 2 == parity:
                value *= 2
                if value > 9:
                    value -= 9
            total += value
        return total % 10 == 0

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


def mask_private_information(content: str) -> str:
    """Public masking entry point for routes that should not construct the AI client."""
    return LLMService.mask_private_information(content)
