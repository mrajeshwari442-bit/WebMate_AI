import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai
from chatbot_config import SCOPE_PROMPT, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)
MODEL = "gemini-3.1-flash-lite"
OUT_OF_SCOPE_MESSAGE = (
    "I'm WebMate AI, focused only on web-based study questions. Please ask me "
    "about HTML, CSS, JavaScript, Flask, HTTP, Web APIs, frontend/backend "
    "development, or another web-related topic."
)


def is_in_scope(message: str) -> bool:
    response = client.models.generate_content(
        model=MODEL,
        contents=message,
        config={
            "system_instruction": SCOPE_PROMPT,
            "temperature": 0,
            "max_output_tokens": 10,
        },
    )
    result = (response.text or "").strip().upper()
    return result == "IN_SCOPE"


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    try:
        if not is_in_scope(message):
            return jsonify({"answer": OUT_OF_SCOPE_MESSAGE})

        response = client.models.generate_content(
            model=MODEL,
            contents=message,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.3,
            },
        )

        answer = response.text or "I couldn't generate a response."
        return jsonify({"answer": answer})

    except Exception:
        return jsonify({
            "error": "Sorry, I couldn't process your request right now."
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
