"""
JSON API #1: Complete Category Classification Pipeline
Combines all 4 categorization endpoints in one service
"""

from flask import Flask, request, jsonify
import requests
import sys
import os
from collections import OrderedDict

# Import mapping files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mapping import shoppingSubcategory_map, itemCategory_map, itemSubcategory_map

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


# ============================================================
# ENDPOINT 1: Shopping Category Classification
# ============================================================

def classify_shopping_category(item_name, description, vendor_category):
    """Classify item into shopping category"""
    prompt = f"""
You are a strict classification bot.
Your ONLY job is to return ONE shopping category.
DO NOT explain. DO NOT add reasoning. DO NOT use multiple lines.

Item: {item_name}
Description: {description}
Vendor Category: {vendor_category}

Allowed categories:
{shoppingCategory}

Return ONLY the category name, nothing else.

Example valid outputs:
fashion
electronics
groceries

Now output ONLY the category name:
"""

    result = run_model(prompt)
    print(f"[Shopping Category] MODEL RAW RESULT: {result}")

    # clean + normalize
    category = result.lower().replace("'", "").replace('"', "").strip()

    # Take only first line if multiple lines returned
    category = category.splitlines()[0].strip()

    # validate
    if category not in shoppingCategory:
        category = ""

    return category


@app.route('/shopping-category', methods=['POST'])
def shopping_category():
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
        "shopping_category": "fashion"
    }
    """
    try:
        data = request.get_json()

        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not item_name:
            return jsonify({"error": "item_name is required"}), 400

        category = classify_shopping_category(item_name, description, vendor_category)

        return jsonify({
            "shopping_category": category
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINT 2: Shopping Subcategory Classification
# ============================================================

def classify_shopping_subcategory(shopping_category, item_name, description, vendor_category):
    """Classify item into shopping subcategory"""

    # Validate input
    if not shopping_category or shopping_category not in shoppingSubcategory_map:
        return ""

    subcategory_list = shoppingSubcategory_map[shopping_category]

    prompt = f"""
You are a strict classification bot.
Your ONLY job is to return ONE shopping subcategory.
DO NOT explain. DO NOT add reasoning. DO NOT use multiple lines.

Item: {item_name}
Description: {description}
Vendor Category: {vendor_category}
Shopping Category: {shopping_category}

Allowed subcategories:
{subcategory_list}

Return ONLY the subcategory name, nothing else.

Example valid outputs:
casual wear
mobile phones
bakery

Now output ONLY the subcategory name:
"""

    result = run_model(prompt)
    print(f"[Shopping Subcategory] MODEL RAW RESULT: {result}")

    # Clean & parse result
    subcategory = result.lower().replace("'", "").replace('"', "").strip()

    # Take only first line if multiple lines returned
    subcategory = subcategory.splitlines()[0].strip()

    # Validate subcategory
    if subcategory not in [s.lower() for s in subcategory_list]:
        subcategory = ""

    return subcategory


@app.route('/shopping-subcategory', methods=['POST'])
def shopping_subcategory():
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
        "shopping_subcategory": "casual wear"
    }
    """
    try:
        data = request.get_json()

        shopping_cat = data.get('shopping_category', '')
        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not shopping_cat:
            return jsonify({"error": "shopping_category is required"}), 400

        subcategory = classify_shopping_subcategory(
            shopping_cat, item_name, description, vendor_category
        )

        return jsonify({
            "shopping_subcategory": subcategory
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINT 3: Item Category Classification
# ============================================================

def classify_item_category(shopping_category, shopping_subcategory, item_name, description, vendor_category):
    """Classify item into item category"""

    # Validate category and subcategory
    if not shopping_category or not shopping_subcategory:
        return ""

    if shopping_category not in itemCategory_map:
        return ""

    if shopping_subcategory not in itemCategory_map[shopping_category]:
        return ""

    item_category_list = itemCategory_map[shopping_category][shopping_subcategory]

    prompt = f"""
You are a strict classification bot.
Your ONLY job is to return ONE item category.
DO NOT explain. DO NOT add reasoning. DO NOT use multiple lines.

Item: {item_name}
Description: {description}
Vendor Category: {vendor_category}
Shopping Category: {shopping_category}
Shopping Subcategory: {shopping_subcategory}

Allowed item categories for {shopping_category} > {shopping_subcategory}:
{item_category_list}

Return ONLY the category name, nothing else.

Example valid outputs:
t-shirt
chocolate cake
smartphone

Now output ONLY the category name:
"""

    result = run_model(prompt)
    print(f"[Item Category] MODEL RAW RESULT: {result}")

    # Parse result
    category = result.lower().replace("'", "").replace('"', "").strip()

    # Take only first line if multiple lines returned
    category = category.splitlines()[0].strip()

    # Validate
    if category not in item_category_list:
        category = ""

    return category


@app.route('/item-category', methods=['POST'])
def item_category():
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
        "item_category": "t-shirt"
    }
    """
    try:
        data = request.get_json()

        shopping_cat = data.get('shopping_category', '')
        shopping_subcat = data.get('shopping_subcategory', '')
        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not shopping_cat or not shopping_subcat:
            return jsonify({"error": "shopping_category and shopping_subcategory are required"}), 400

        category = classify_item_category(
            shopping_cat, shopping_subcat, item_name, description, vendor_category
        )

        return jsonify({
            "item_category": category
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINT 4: Item Subcategory Classification
# ============================================================

def classify_item_subcategory(shopping_category, shopping_subcategory, item_category, item_name, description, vendor_category):
    """Classify item into item subcategory"""

    # Validate required fields
    if not shopping_category or not shopping_subcategory or not item_category:
        return ""

    if shopping_category not in itemSubcategory_map or item_category not in itemSubcategory_map[shopping_category]:
        return ""

    item_subcategory_list = itemSubcategory_map[shopping_category][item_category]

    prompt = f"""
You are a strict classification bot.
Your ONLY job is to return ONE item subcategory.
DO NOT explain. DO NOT add reasoning. DO NOT use multiple lines.

Item: {item_name}
Description: {description}
Vendor Category: {vendor_category}
Current Classification Path:
- Shopping Category: {shopping_category}
- Shopping Subcategory: {shopping_subcategory}
- Item Category: {item_category}

Allowed subcategories for {shopping_category} > {item_category}:
{item_subcategory_list}

Return ONLY the subcategory name, nothing else.

Example valid outputs:
sweatshirt
running shoes
vitamin d

Now output ONLY the subcategory name:
"""

    result = run_model(prompt)
    print(f"[Item Subcategory] MODEL RAW RESULT: {result}")

    # Parse result
    subcategory = result.lower().replace("'", "").replace('"', "").strip()

    # Take only first line if multiple lines returned
    subcategory = subcategory.splitlines()[0].strip()

    # Validate
    if subcategory not in item_subcategory_list:
        subcategory = ""

    return subcategory


@app.route('/item-subcategory', methods=['POST'])
def item_subcategory():
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
        "item_subcategory": "t-shirt"
    }
    """
    try:
        data = request.get_json()

        shopping_cat = data.get('shopping_category', '')
        shopping_subcat = data.get('shopping_subcategory', '')
        item_cat = data.get('item_category', '')
        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not shopping_cat or not shopping_subcat or not item_cat:
            return jsonify({
                "error": "shopping_category, shopping_subcategory, and item_category are required"
            }), 400

        subcategory = classify_item_subcategory(
            shopping_cat, shopping_subcat, item_cat,
            item_name, description, vendor_category
        )

        return jsonify({
            "item_subcategory": subcategory
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# UNIFIED ENDPOINT: All Classifications in One Call
# ============================================================

@app.route('/classify-all', methods=['POST'])
def classify_all():
    """
    Run all 4 classifications sequentially and return complete categorization

    Input JSON:
    {
        "item_name": "Item name here",
        "description": "Item description",
        "vendor_category": "Vendor category"
    }

    Returns:
    {
        "shopping_category": "fashion",
        "shopping_subcategory": "casual wear",
        "item_category": "top",
        "item_subcategory": "t-shirt"
    }
    """
    try:
        data = request.get_json()

        item_name = data.get('item_name', '')
        description = data.get('description', '')
        vendor_category = data.get('vendor_category', '')

        if not item_name:
            return jsonify({"error": "item_name is required"}), 400

        # Step 1: Shopping Category
        shopping_cat = classify_shopping_category(item_name, description, vendor_category)
        if not shopping_cat:
            result = OrderedDict([
                ("shopping_category", ""),
                ("shopping_subcategory", ""),
                ("item_category", ""),
                ("item_subcategory", "")
            ])
            return jsonify(result)

        # Step 2: Shopping Subcategory
        shopping_subcat = classify_shopping_subcategory(
            shopping_cat, item_name, description, vendor_category
        )
        if not shopping_subcat:
            result = OrderedDict([
                ("shopping_category", shopping_cat),
                ("shopping_subcategory", ""),
                ("item_category", ""),
                ("item_subcategory", "")
            ])
            return jsonify(result)

        # Step 3: Item Category
        item_cat = classify_item_category(
            shopping_cat, shopping_subcat, item_name, description, vendor_category
        )
        if not item_cat:
            result = OrderedDict([
                ("shopping_category", shopping_cat),
                ("shopping_subcategory", shopping_subcat),
                ("item_category", ""),
                ("item_subcategory", "")
            ])
            return jsonify(result)

        # Step 4: Item Subcategory
        item_subcat = classify_item_subcategory(
            shopping_cat, shopping_subcat, item_cat,
            item_name, description, vendor_category
        )

        result = OrderedDict([
            ("shopping_category", shopping_cat),
            ("shopping_subcategory", shopping_subcat),
            ("item_category", item_cat),
            ("item_subcategory", item_subcat)
        ])
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Utility Endpoints
# ============================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Complete Category Classification API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "Complete Category Classification API",
        "version": "1.0.0",
        "description": "Unified API for all 4 categorization endpoints",
        "endpoints": {
            "/classify-all": "Run all 4 classifications in one call (POST) - RECOMMENDED",
            "/shopping-category": "Classify item into shopping category (POST)",
            "/shopping-subcategory": "Classify item into shopping subcategory (POST)",
            "/item-category": "Classify item into item category (POST)",
            "/item-subcategory": "Classify item into item subcategory (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Complete Category Classification API")
    print("="*70)
    print("\nEndpoints:")
    print("  POST /classify-all         - ALL 4 classifications in one call (RECOMMENDED)")
    print("  POST /shopping-category    - Step 1: Classify shopping category")
    print("  POST /shopping-subcategory - Step 2: Classify shopping subcategory")
    print("  POST /item-category        - Step 3: Classify item category")
    print("  POST /item-subcategory     - Step 4: Classify item subcategory")
    print("  GET  /health               - Health check")
    print("\n" + "="*70)
    print("\nStarting API on http://localhost:6001")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6001)
