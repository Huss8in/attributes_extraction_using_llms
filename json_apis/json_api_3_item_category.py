"""
JSON API #3: Item Category Classification
Accepts JSON input and returns item category as string
"""

from flask import Flask, request, jsonify
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mapping import itemCategory_map

app = Flask(__name__)

# Model configuration
API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "phi4:latest"


def run_model(prompt):
    """Run the AI model with the given prompt"""
    payload = {"model": MODEL_NAME, "prompt": prompt, "max_tokens": 150, "stream": False}
    r = requests.post(API_URL, json=payload)
    r.raise_for_status()
    data = r.json()
    return data["response"].strip()


def classify_item_category(shopping_category, shopping_subcategory, item_name, description, vendor_category):
    """Classify item into item category with strict format"""

    # Validate category and subcategory
    if not shopping_category or not shopping_subcategory:
        return "", 0

    if shopping_category not in itemCategory_map:
        return "", 0

    if shopping_subcategory not in itemCategory_map[shopping_category]:
        return "", 0

    item_category_list = itemCategory_map[shopping_category][shopping_subcategory]

    prompt = f"""
    You are a strict classification bot.
    Your ONLY job is to return ONE item category and ONE confidence.
    DO NOT explain. DO NOT add reasoning. DO NOT use multiple lines.

    Item: {item_name}
    Description: {description}
    Vendor Category: {vendor_category}
    Shopping Category: {shopping_category}
    Shopping Subcategory: {shopping_subcategory}

    Allowed item categories for {shopping_category} > {shopping_subcategory}:
    {item_category_list}

    Output format (MUST follow exactly):
    <category>|confidence:<number>%

    Example valid outputs:
    t-shirt|confidence:95%
    chocolate cake|confidence:88%

    Now output ONLY one valid line:
    """

    result = run_model(prompt)
    result = result.lower().replace("'", "").replace('"', "").strip()
    print(f"MODEL RAW RESULT: {result}")

    # Parse result
    if "|confidence" in result:
        parts = result.split("|confidence")
        category = parts[0].strip().replace(":", "")
        confidence = parts[1].replace("%", "").replace(":", "").strip()
        try:
            confidence = int(confidence)
        except:
            confidence = 0
    else:
        category = result.strip()
        confidence = 0

    # Validate
    if category not in item_category_list:
        category = ""
        confidence = 0

    return category, confidence


@app.route('/classify', methods=['POST'])
def classify():
    """
    Classify item into item category

    Input JSON:
    {
        "shopping_category": "fashion",
        "shopping_subcategory": "casual wear",
        "item_name": "Item name here",
        "description": "Item description",
        "vendor_category": "Vendor category"
    }

    Returns:
    {
        "item_category": "t-shirt",
        "confidence": 95
    }
    """
    try:
        data = request.get_json()

        shopping_category = data.get('shopping_category', '')
        shopping_subcategory = data.get('shopping_subcategory', '')
        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not shopping_category or not shopping_subcategory:
            return jsonify({"error": "shopping_category and shopping_subcategory are required"}), 400

        category, confidence = classify_item_category(
            shopping_category, shopping_subcategory, item_name, description, vendor_category
        )

        return jsonify({
            "item_category": category,
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON Item Category Classification API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON Item Category Classification API",
        "version": "1.0.0",
        "endpoints": {
            "/classify": "Classify item into item category (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON Item Category Classification API")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /classify - Classify item into item category")
    print("  GET  /health   - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6003")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6003)
