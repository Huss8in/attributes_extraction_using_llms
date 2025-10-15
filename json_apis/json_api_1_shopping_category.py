"""
JSON API #1: Shopping Category Classification
Accepts JSON input and returns shopping category as string
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Model configuration
API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "phi4:latest"

# Shopping categories
shoppingCategory = [
    "stationary", "restaurants", "electronics", "pharmacies", "pet care", "home and garden",
    "beauty", "entertainment", "health and nutrition", "groceries", "fashion",
    "automotive", "sports", "kids", "flowers and gifts"
]


def run_model(prompt):
    """Run the AI model with the given prompt"""
    payload = {"model": MODEL_NAME, "prompt": prompt, "max_tokens": 200, "stream": False}
    r = requests.post(API_URL, json=payload)
    r.raise_for_status()
    data = r.json()
    return data["response"].strip()


def classify_shopping_category(item_name, description, vendor_category):
    """Classify item into shopping category with confidence"""
    prompt = f"""
You are a strict classification bot.
Your ONLY job is to return ONE shopping category and ONE confidence.
DO NOT explain. DO NOT add reasoning. DO NOT use multiple lines.

Item: {item_name}
Description: {description}
Vendor Category: {vendor_category}

Allowed categories:
{shoppingCategory}

Output format (MUST follow exactly):
<category>|confidence:<number>%

Example valid outputs:
fashion|confidence:95%
electronics|confidence:88%

Now output ONLY one valid line:
"""

    result = run_model(prompt)
    print(f"MODEL RAW RESULT: {result}")

    # clean + normalize
    result = result.lower().replace("'", "").replace('"', "").strip()

    # extract only first valid match
    import re
    matches = re.findall(r"([a-z\s&]+)\|confidence[:\s]*([0-9]{1,3})%", result)
    if matches:
        category = matches[0][0].strip()
        confidence = int(matches[0][1])
    else:
        category, confidence = "", 0

    # validate
    if category not in shoppingCategory:
        category, confidence = "", 0

    return category, confidence


@app.route('/classify', methods=['POST'])
def classify():
    """
    Classify item into shopping category

    Input JSON:
    {
        "item_name": "Item name here",
        "description": "Item description",
        "vendor_category": "Vendor category"
    }

    Returns:
    {
        "shopping_category": "fashion",
        "confidence": 95
    }
    """
    try:
        data = request.get_json()

        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not item_name:
            return jsonify({"error": "item_name is required"}), 400

        category, confidence = classify_shopping_category(item_name, description, vendor_category)

        return jsonify({
            "shopping_category": category,
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON Shopping Category Classification API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON Shopping Category Classification API",
        "version": "1.0.0",
        "endpoints": {
            "/classify": "Classify item into shopping category (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON Shopping Category Classification API")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /classify - Classify item into shopping category")
    print("  GET  /health   - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6001")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6001)
