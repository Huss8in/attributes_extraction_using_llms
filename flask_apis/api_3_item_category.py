"""
Flask API #7: Item Category Classification
Classifies items into item categories (Level 3) based on shopping category and subcategory
"""

from flask import Flask, request, jsonify
import pandas as pd
import requests
import os
import sys
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
    """Classify item into item category (Level 3) with strict format"""

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


@app.route('/get_item_category', methods=['POST'])
def get_item_category():
    """
    Process CSV for item category classification.
    Input JSON:
    {
        "csv_path": "path/to/input.csv",
        "output_path": "optional/output.csv"
    }
    """
    try:
        data = request.get_json()
        csv_path = data.get("csv_path")
        output_path = data.get("output_path", csv_path.replace(".csv", "_item_category.csv"))

        if not csv_path:
            return jsonify({"error": "csv_path is required"}), 400
        if not os.path.exists(csv_path):
            return jsonify({"error": f"File not found: {csv_path}"}), 404

        df = pd.read_csv(csv_path)

        # Fix for duplicated headers
        if df.iloc[0].equals(df.columns):
            df.columns = df.iloc[0]
            df = df.drop([0, 1]).reset_index(drop=True)

        # Apply classification
        results = df.apply(
            lambda row: pd.Series(classify_item_category(
                row.get("shoppingCategory", ""),
                row.get("shoppingSubcategory", ""),
                row.get("Item (EN)", ""),
                row.get("Description (EN)", ""),
                row.get("Category/Department (EN)", "")
            )),
            axis=1
        )
        df[["itemCategory", "itemCategory_confidence"]] = results

        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return jsonify({
            "success": True,
            "message": "Item category classification completed successfully",
            "output_path": output_path,
            "processed_rows": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Item Category Classification API"})


if __name__ == '__main__':
    print("Starting Item Category Classification API...")
    print("API will be available at http://localhost:5003/get_item_category")
    app.run(debug=True, host='0.0.0.0', port=5003)
