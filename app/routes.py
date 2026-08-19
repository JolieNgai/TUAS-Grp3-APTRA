from flask import Blueprint, render_template, request, current_app

from app.services.llm_service import LLMService

MAX_PROMPT_LENGTH = 10000
MAX_CONTEXT_LENGTH = 5000
ALLOWED_TONES = {"professional", "casual", "formal", "friendly", "diplomatic"}
ALLOWED_LENGTHS = {"short", "medium", "long"}

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def index():
    result = None
    prompt = ""
    tone = ""
    length = ""
    additional_context = ""

    if request.method == "POST":
        raw_prompt = request.form.get("prompt", "").strip()
        tone = request.form.get("tone", "").strip()
        length = request.form.get("length", "").strip()
        raw_additional_context = request.form.get("additional_context", "").strip()

        # Preserve exactly what the user entered in the form. LLMService masks
        # supported identifiers only when constructing the external AI prompt.
        prompt = raw_prompt
        additional_context = raw_additional_context

        if prompt and tone and length:
            if len(raw_prompt) > MAX_PROMPT_LENGTH:
                result = f"Input is too long. Please limit your email to {MAX_PROMPT_LENGTH} characters."
            elif tone.lower() not in ALLOWED_TONES:
                current_app.logger.warning(f"Invalid tone attempted: {tone}")
                result = "Invalid tone selected. Please choose a valid option."
            elif length.lower() not in ALLOWED_LENGTHS:
                current_app.logger.warning(f"Invalid length attempted: {length}")
                result = "Invalid length selected. Please choose a valid option."
            elif len(raw_additional_context) > MAX_CONTEXT_LENGTH:
                result = f"Additional context is too long. Please limit it to {MAX_CONTEXT_LENGTH} characters."
            else:
                try:
                    llm_service = LLMService()
                    final_prompt = llm_service.build_reply_prompt(prompt, tone, length, additional_context)
                    result = llm_service.generate_response(final_prompt)
                except ValueError as exc:
                    current_app.logger.error(f"Configuration error: {exc}")
                    result = "Unable to generate a reply right now. Please check your configuration."
                except Exception as exc:
                    current_app.logger.error(f"LLM generation failed: {exc}")
                    result = "An error occurred while generating the reply. Please try again later."

    return render_template("index.html", prompt=prompt, result=result, tone=tone, length=length, additional_context=additional_context)
