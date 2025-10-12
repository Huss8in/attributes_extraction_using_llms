"""
Flask API #8: English → Arabic Translation (single text)
Translates plain text from English to Arabic
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "aya:8b"


def run_model(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": 200,
        "stream": False
    }
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()["response"].strip()


def translate_to_arabic(text: str) -> str:
    if not text or text.strip().lower() == "empty":
        return ""
    prompt = (
        "You are a professional English to Arabic translator for e-commerce. "
        "Translate the following text into Arabic. Respond with Arabic text only, no explanations.\n\n"
        + text
    )
    try:
        return run_model(prompt)
    except Exception as e:
        print(f"Translation error: {e}")
        return ""


@app.route("/translate", methods=["POST"])
def translate_endpoint():
    """
    Translate a single text string from English to Arabic.

    Input JSON:
    {
        "text": "Your text here"
    }
    """
    data = request.get_json(force=True)
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "Missing 'text' field"}), 400

    translation = translate_to_arabic(text)

    return jsonify({"translation": translation})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "Arabic Translation API"})


if __name__ == "__main__":
    print("Starting Arabic Translation API...")
    print("API will be available at http://localhost:5008/translate")
    app.run(debug=True, host="0.0.0.0", port=5008)
