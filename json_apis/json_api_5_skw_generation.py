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

# ==================================================================================== #
def generate_skw(item_name, item_category):
    """Fast and accurate SKW generator ensuring core product noun first"""

    prompt = f"""
You are a strict e-commerce keyword generator.
Generate concise keyword phrases (1 to 5 only) that customers would type when shopping for an item online.
Use ONLY the item name and category to decide what keywords make sense.

Item Name: {item_name}
Item Category: {item_category}

Rules:
- Each keyword phrase must contain the core product noun (like pants, top, jacket, dress, etc.).
- The first keyword phrase MUST be only the core product noun.
- Avoid adjectives or promotional words unless part of the item name.
- Each phrase should be short (max 3 words).
- Output 1 to 5 keyword phrases, comma-separated, in Title Case.
- Output ONLY the keyword phrases.
"""

    result = run_model(prompt)
    print("*************************")
    print(result)
    print("*************************")

    # Normalize and split
    result = result.replace("\n", "").replace('"', "").replace("'", "").strip().lower()
    keywords = [k.strip() for k in result.split(",") if k.strip()]

    # Identify the main product noun (last word of item name)
    product_noun = item_name.lower().replace("-", " ").split()[-1]

    # Filter to include only phrases that contain the noun
    keywords = [kw for kw in keywords if product_noun in kw]

    # Always ensure noun is first
    if not keywords or keywords[0] != product_noun:
        keywords = [product_noun] + [kw for kw in keywords if kw != product_noun]

    # Remove duplicates while preserving order, limit to 5
    seen = set()
    final_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            final_keywords.append(kw)
        if len(final_keywords) == 5:
            break

    # Return formatted string
    final_result = ", ".join([kw.title() for kw in final_keywords])
    print(f"MODEL RAW RESULT: {final_result}")
    return final_result


# ==================================================================================== #

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()

        item_name = data.get('item_name', '')
        item_category = data.get('item_category', '')

        if not item_category:
            return jsonify({"error": "item_category is required"}), 400

        skw = generate_skw(item_name, item_category)

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
