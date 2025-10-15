"""
JSON API #5: SKW (Search Keywords) Generation
Accepts JSON input and returns SKW as string
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Model configuration
API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "phi4:latest"


def run_model(prompt):
    """Run the AI model with the given prompt"""
    payload = {"model": MODEL_NAME, "prompt": prompt, "max_tokens": 200, "stream": False}
    r = requests.post(API_URL, json=payload)
    r.raise_for_status()
    return r.json()["response"].strip()


def generate_skw(item_name, description, item_category):
    """Generate strict Search Keywords (SKW) for an item"""

    input_text = f"Item: {item_name}\nDescription: {description}\nItem Category: {item_category}"

    prompt = f"""
You are a strict e-commerce keyword generator.
Generate exactly 5 keyword phrases for the item below. FOLLOW THESE RULES STRICTLY:

Item Data:
{input_text}

Rules:
1. Output exactly 5 phrases separated by commas, no numbering or extra text
2. The first phrase must be ONLY the item category: {item_category}
3. All other phrases must end with the item category: {item_category}
4. Each phrase must be maximum 3 words
5. Format: modifier + modifier + item category
6. Use tangible features, proper nouns, or item attributes as modifiers
7. Do NOT include sentiments, numbers, dates, symbols, or extra words
8. Return everything in lowercase
9. STRICTLY follow the format. Do not add explanations or newlines

Output ONLY:
"""

    result = run_model(prompt)
    result = result.replace("\n", "").replace('"', "").replace("'", "").strip().lower()
    print(f"MODEL RAW RESULT: {result}")
    return result


@app.route('/generate', methods=['POST'])
def generate():
    """
    Generate SKW for item

    Input JSON:
    {
        "item_name": "Item name here",
        "description": "Item description",
        "item_category": "t-shirt"
    }

    Returns:
    {
        "skw": "t-shirt, cotton t-shirt, casual t-shirt, ..."
    }
    """
    try:
        data = request.get_json()

        item_name = data.get('item_name', '')
        description = data.get('description', '')
        item_category = data.get('item_category', '')

        if not item_category:
            return jsonify({"error": "item_category is required"}), 400

        skw = generate_skw(item_name, description, item_category)

        return jsonify({"skw": skw})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON SKW Generation API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON SKW Generation API",
        "version": "1.0.0",
        "endpoints": {
            "/generate": "Generate SKW for item (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON SKW Generation API")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /generate - Generate SKW for item")
    print("  GET  /health   - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6005")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6005)
