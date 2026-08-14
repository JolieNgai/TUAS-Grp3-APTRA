from flask import Blueprint, render_template, request

from app.services.llm_service import LLMService

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
            try:
                llm_service = LLMService()
                result = llm_service.generate_response(prompt, tone, length)
            except ValueError as exc:
                result = str(exc)
            except Exception as exc:
                result = f"Unable to generate a reply right now: {exc}"

    return render_template("index.html", prompt=prompt, result=result, tone=tone, length=length)
