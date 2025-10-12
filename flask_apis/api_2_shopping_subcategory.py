"""
Flask API #6: Shopping Subcategory Classification
Classifies items into shopping subcategories based on shopping category
"""

from flask import Flask, request, jsonify
import pandas as pd
import requests
import os
import sys

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
    """Classify item into shopping subcategory (Level 2) with confidence"""

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


@app.route('/get_subshopping_category', methods=['POST'])
def get_shopping_subcategory():
    """
    Process CSV file with shopping subcategory classification

    Expects JSON with:
    - csv_path: path to input CSV file
    - output_path: path to save output CSV file (optional)
    """
    try:
        data = request.get_json()
        csv_path = data.get('csv_path')
        output_path = data.get('output_path', csv_path.replace('.csv', '_shopping_subcategory.csv'))

        if not csv_path:
            return jsonify({"error": "csv_path is required"}), 400
        if not os.path.exists(csv_path):
            return jsonify({"error": f"File not found: {csv_path}"}), 404

        df = pd.read_csv(csv_path)

        # Handle headers if duplicated
        if df.iloc[0].equals(df.columns):
            df.columns = df.iloc[0]
            df = df.drop([0, 1]).reset_index(drop=True)

        # Apply model classification
        results = df.apply(
            lambda row: pd.Series(classify_shopping_subcategory(
                row.get("shoppingCategory", ""),
                row.get("Item (EN)", ""),
                row.get("Description (EN)", ""),
                row.get("Category/Department (EN)", "")
            )),
            axis=1
        )

        df[["shoppingSubcategory", "subcategory_confidence"]] = results

        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        return jsonify({
            "success": True,
            "message": "Shopping subcategory classification completed",
            "output_path": output_path,
            "processed_rows": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Shopping Subcategory Classification API"})


if __name__ == '__main__':
    print("Starting Shopping Subcategory Classification API...")
    print("API will be available at http://localhost:5002")
    app.run(debug=True, host='0.0.0.0', port=5002)
