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
        tone = request.form.get("tone", "").strip()
        length = request.form.get("length", "").strip()

        if prompt and tone and length:
            try:
                llm_service = LLMService()
                final_prompt = llm_service.build_reply_prompt(prompt, tone, length)
                result = llm_service.generate_response(final_prompt)
            except ValueError:
                result = "Please configure the OPENAI_API_KEY in your environment before generating a reply."
            except Exception as exc:
                result = f"Unable to generate a reply right now: {exc}"

    return render_template("index.html", prompt=prompt, result=result, tone=tone, length=length)
