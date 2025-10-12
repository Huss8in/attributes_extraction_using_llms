"""
Flask API #8: Item Subcategory Classification
Classifies items into item subcategories (Level 4) based on shopping category and item category
"""

from flask import Flask, request, jsonify
import pandas as pd
import requests
import os
import sys
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
    """Classify item into item subcategory (Level 4) with strict format"""

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


@app.route('/get_item_subcategory', methods=['POST'])
def get_item_subcategory():
    """
    Process CSV for item subcategory classification.
    Input JSON:
    {
        "csv_path": "path/to/input.csv",
        "output_path": "optional/output.csv"
    }
    """
    try:
        data = request.get_json()
        csv_path = data.get("csv_path")
        output_path = data.get("output_path", csv_path.replace(".csv", "_item_subcategory.csv"))

        if not csv_path:
            return jsonify({"error": "csv_path is required"}), 400
        if not os.path.exists(csv_path):
            return jsonify({"error": f"File not found: {csv_path}"}), 404

        df = pd.read_csv(csv_path)

        # Fix duplicated headers
        if df.iloc[0].equals(df.columns):
            df.columns = df.iloc[0]
            df = df.drop([0, 1]).reset_index(drop=True)

        # Apply classification
        results = df.apply(
            lambda row: pd.Series(classify_item_subcategory(
                row.get("shoppingCategory", ""),
                row.get("shoppingSubcategory", ""),
                row.get("itemCategory", ""),
                row.get("Item (EN)", ""),
                row.get("Description (EN)", ""),
                row.get("Category/Department (EN)", "")
            )),
            axis=1
        )
        df[["itemSubcategory", "itemSubcategory_confidence"]] = results

        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return jsonify({
            "success": True,
            "message": "Item subcategory classification completed successfully",
            "output_path": output_path,
            "processed_rows": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Item Subcategory Classification API"})


if __name__ == '__main__':
    print("Starting Item Subcategory Classification API...")
    print("API will be available at http://localhost:5004/get_item_subcategory")
    app.run(debug=True, host='0.0.0.0', port=5004)
