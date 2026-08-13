from flask import Blueprint, render_template, request

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
            # TODO: Backend will integrate LLM here with tone and length parameters
            # The LLM should generate a reply to the received email with specified tone and length
            result = "Backend processing coming soon..."

    return render_template("index.html", prompt=prompt, result=result)
