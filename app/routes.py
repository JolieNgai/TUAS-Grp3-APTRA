from flask import Blueprint, render_template, request

from app.services.llm_service import LLMService

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def index():
    result = None
    prompt = ""

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()

        if prompt:
            try:
                result = LLMService().generate_response(prompt)
            except Exception as exc:
                result = f"Error: {exc}"

    return render_template("index.html", prompt=prompt, result=result)
