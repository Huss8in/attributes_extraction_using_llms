"""
JSON API #7: AI Attributes Extraction
Accepts JSON input and returns AI attributes as string
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Model configuration
API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "phi4:latest"


def run_model(prompt):
    """Run the AI model with the given prompt"""
    payload = {"model": MODEL_NAME, "prompt": prompt, "max_tokens": 300, "stream": False}
    r = requests.post(API_URL, json=payload)
    r.raise_for_status()
    return r.json()["response"].strip()


def extract_ai_attributes(item_name, description, vendor_category, shopping_category, shopping_subcategory, item_category):
    """Extract AI Attributes with strict formatting"""

    input_text = f"""Item Name: {item_name}
Description: {description}
Vendor Category: {vendor_category}
Shopping Category: {shopping_category}
Shopping Subcategory: {shopping_subcategory}
Item Category: {item_category}"""

    prompt = f"""
You are a strict AI attribute extractor for e-commerce products.
Analyze the item below and extract ONLY attributes that can be clearly inferred.
Do NOT guess, do NOT add explanations, do NOT include extra text.
Leave unknown attributes empty.

{input_text}

INSTRUCTIONS:
- Fill only known attributes; leave others empty
- Use concise English values
- Gender: choose strictly from ["Women", "Men", "Unisex women, Unisex men", "Girls", "Boys", "Unisex girls, unisex boys"]
- Generic Name: use the item category if possible
- Color: infer from name or description
- Product Name: concise, not verbatim copy of item name

OUTPUT FORMAT (exactly, no deviations):

Gender:
Age:
Brand:
Generic Name:
Product Name:
Size:
Measurements:
Features:
Types of Fashion Styles:
Gem Stones:
Birth Stones:
Material:
Color:
Pattern:
Occasion:
Activity:
Season:
Country of origin:

Output ONLY the above format. NO extra lines or explanations.
"""

    result = run_model(prompt)
    result = result.replace("\r", "").strip()
    print(f"MODEL RAW RESULT: {result}")
    return result


@app.route('/extract', methods=['POST'])
def extract():
    """
    Extract AI attributes for item

    Input JSON:
    {
        "item_name": "Item name here",
        "description": "Item description",
        "vendor_category": "Vendor category",
        "shopping_category": "fashion",
        "shopping_subcategory": "casual wear",
        "item_category": "t-shirt"
    }

    Returns:
    {
        "ai_attributes": "Gender: Women\nAge: Adult\n..."
    }
    """
    try:
        data = request.get_json()

        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')
        shopping_category = data.get('shopping_category', '')
        shopping_subcategory = data.get('shopping_subcategory', '')
        item_category = data.get('item_category', '')

        attributes = extract_ai_attributes(
            item_name, description, vendor_category,
            shopping_category, shopping_subcategory, item_category
        )

        return jsonify({"ai_attributes": attributes})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON AI Attributes Extraction API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON AI Attributes Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "/extract": "Extract AI attributes for item (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON AI Attributes Extraction API")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /extract - Extract AI attributes for item")
    print("  GET  /health  - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6007")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6007)
