"""
JSON API #4: Item Subcategory Classification
Accepts JSON input and returns item subcategory as string
"""

from flask import Flask, request, jsonify
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mapping import itemSubcategory_map

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


def classify_item_subcategory(shopping_category, shopping_subcategory, item_category, item_name, description, vendor_category):
    """Classify item into item subcategory with strict format"""

    # Validate required fields
    if not shopping_category or not shopping_subcategory or not item_category:
        return "", 0

    if shopping_category not in itemSubcategory_map or item_category not in itemSubcategory_map[shopping_category]:
        return "", 0

    item_subcategory_list = itemSubcategory_map[shopping_category][item_category]

    prompt = f"""
You are a strict classification bot.
Return ONLY ONE subcategory and confidence. No explanation, no extra lines.

Item: {item_name}
Description: {description}
Vendor Category: {vendor_category}
Current Classification Path:
- Shopping Category: {shopping_category}
- Shopping Subcategory: {shopping_subcategory}
- Item Category: {item_category}

Allowed subcategories for {shopping_category} > {item_category}:
{item_subcategory_list}

Output format (MUST follow exactly):
<subcategory>|confidence:<number>%

Example:
sweatshirt|confidence:90%

Output ONLY one line:
"""

    result = run_model(prompt)
    result = result.lower().replace("'", "").replace('"', "").strip()
    print(f"MODEL RAW RESULT: {result}")

    # Parse result
    if "|confidence" in result:
        parts = result.split("|confidence")
        subcategory = parts[0].strip().replace(":", "")
        confidence = parts[1].replace("%", "").replace(":", "").strip()
        try:
            confidence = int(confidence)
        except:
            confidence = 0
    else:
        subcategory = result.strip()
        confidence = 0

    # Validate
    if subcategory not in item_subcategory_list:
        subcategory = ""
        confidence = 0

    return subcategory, confidence


@app.route('/classify', methods=['POST'])
def classify():
    """
    Classify item into item subcategory

    Input JSON:
    {
        "shopping_category": "fashion",
        "shopping_subcategory": "casual wear",
        "item_category": "top",
        "item_name": "Item name here",
        "description": "Item description",
        "vendor_category": "Vendor category"
    }

    Returns:
    {
        "item_subcategory": "t-shirt",
        "confidence": 90
    }
    """
    try:
        data = request.get_json()

        shopping_category = data.get('shopping_category', '')
        shopping_subcategory = data.get('shopping_subcategory', '')
        item_category = data.get('item_category', '')
        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not shopping_category or not shopping_subcategory or not item_category:
            return jsonify({
                "error": "shopping_category, shopping_subcategory, and item_category are required"
            }), 400

        subcategory, confidence = classify_item_subcategory(
            shopping_category, shopping_subcategory, item_category,
            item_name, description, vendor_category
        )

        return jsonify({
            "item_subcategory": subcategory,
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON Item Subcategory Classification API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON Item Subcategory Classification API",
        "version": "1.0.0",
        "endpoints": {
            "/classify": "Classify item into item subcategory (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON Item Subcategory Classification API")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /classify - Classify item into item subcategory")
    print("  GET  /health   - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6004")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6004)
