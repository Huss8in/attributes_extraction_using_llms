"""
JSON API #2: Shopping Subcategory Classification
Accepts JSON input and returns shopping subcategory as string
"""

from flask import Flask, request, jsonify
import requests
import sys
import os

# Import mapping file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mapping import shoppingSubcategory_map

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


def classify_shopping_subcategory(shopping_category, item_name, description, vendor_category):
    """Classify item into shopping subcategory with confidence"""

    # Validate input
    if not shopping_category or shopping_category not in shoppingSubcategory_map:
        return "", 0

    subcategory_list = shoppingSubcategory_map[shopping_category]

    prompt = f"""
You are a strict classification bot.
Your ONLY job is to return ONE shopping subcategory and ONE confidence.
DO NOT explain. DO NOT add reasoning. DO NOT use multiple lines.

Item: {item_name}
Description: {description}
Vendor Category: {vendor_category}
Shopping Category: {shopping_category}

Allowed subcategories:
{subcategory_list}

Output format (MUST follow exactly):
<subcategory>|confidence:<number>%

Example valid outputs:
casual wear|confidence:95%
mobile phones|confidence:88%

If none fit, output:
|confidence:0%

Now output ONLY one valid line:
"""

    result = run_model(prompt)
    result = result.lower().strip().splitlines()[0]
    print(f"MODEL RAW RESULT: {result}")

    # Clean & parse result
    result = result.replace("'", "").replace('"', "").replace(":", "").strip()

    if "|confidence" in result:
        parts = result.split("|confidence")
        subcategory = parts[0].strip()
        confidence = parts[1].strip().replace("%", "").strip()
        try:
            confidence = int(confidence)
        except:
            confidence = 0
    else:
        subcategory = result.strip()
        confidence = 0

    # Validate subcategory
    if subcategory not in [s.lower() for s in subcategory_list]:
        subcategory = ""
        confidence = 0

    return subcategory, confidence


@app.route('/classify', methods=['POST'])
def classify():
    """
    Classify item into shopping subcategory

    Input JSON:
    {
        "shopping_category": "fashion",
        "item_name": "Item name here",
        "description": "Item description",
        "vendor_category": "Vendor category"
    }

    Returns:
    {
        "shopping_subcategory": "casual wear",
        "confidence": 92
    }
    """
    try:
        data = request.get_json()

        shopping_category = data.get('shopping_category', '')
        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not shopping_category:
            return jsonify({"error": "shopping_category is required"}), 400

        subcategory, confidence = classify_shopping_subcategory(
            shopping_category, item_name, description, vendor_category
        )

        return jsonify({
            "shopping_subcategory": subcategory,
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON Shopping Subcategory Classification API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON Shopping Subcategory Classification API",
        "version": "1.0.0",
        "endpoints": {
            "/classify": "Classify item into shopping subcategory (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON Shopping Subcategory Classification API")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /classify - Classify item into shopping subcategory")
    print("  GET  /health   - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6002")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6002)
