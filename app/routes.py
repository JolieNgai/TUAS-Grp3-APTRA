from flask import Blueprint, render_template, request, current_app

from app.services.llm_service import LLMService

MAX_PROMPT_LENGTH = 10000

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def index():
    result = None
    prompt = ""
    tone = ""
    length = ""

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        tone = request.form.get("tone", "").strip().lower()
        length = request.form.get("length", "").strip().lower()

        if prompt and tone and length:
            if len(prompt) > MAX_PROMPT_LENGTH:
                result = f"Input is too long. Please limit your email to {MAX_PROMPT_LENGTH} characters."
            else:
                try:
                    llm_service = LLMService()
                    result = llm_service.generate_response(prompt, tone, length)
                except ValueError as exc:
                    current_app.logger.error(f"Configuration error: {exc}")
                    result = "Unable to generate a reply right now. Please check your configuration."
                except Exception as exc:
                    current_app.logger.error(f"LLM generation failed: {exc}")
                    result = "An error occurred while generating the reply. Please try again later."

    return render_template("index.html", prompt=prompt, result=result, tone=tone, length=length)
