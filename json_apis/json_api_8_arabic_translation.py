"""
JSON API #8: Arabic Translation
Accepts JSON input and returns Arabic translation as string
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Model configuration
API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "aya:8b"


def run_model(prompt):
    """Run the AI model with the given prompt"""
    payload = {"model": MODEL_NAME, "prompt": prompt, "max_tokens": 200, "stream": False}
    r = requests.post(API_URL, json=payload)
    r.raise_for_status()
    return r.json()["response"].strip()


def translate_to_arabic(text):
    """Translate text from English to Arabic"""
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


@app.route('/translate', methods=['POST'])
def translate():
    """
    Translate text from English to Arabic

    Input JSON:
    {
        "text": "Your text here"
    }

    Returns:
    {
        "translation": "الترجمة العربية"
    }
    """
    try:
        data = request.get_json()

        text = data.get('text', '')

        if not text:
            return jsonify({"error": "text is required"}), 400

        translation = translate_to_arabic(text)

        return jsonify({"translation": translation})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON Arabic Translation API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON Arabic Translation API",
        "version": "1.0.0",
        "endpoints": {
            "/translate": "Translate text to Arabic (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON Arabic Translation API")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /translate - Translate text to Arabic")
    print("  GET  /health    - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6008")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6008)
