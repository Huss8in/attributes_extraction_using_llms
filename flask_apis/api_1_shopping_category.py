"""
Flask API #5: Shopping Category Classification
Classifies items into shopping categories with confidence scores
"""

from flask import Flask, request, jsonify
import pandas as pd
import requests
import os

app = Flask(__name__)

# Model configuration
API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "phi4:latest"

# Shopping categories from mapping.py
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

# ======================================================= #
def classify_shopping_category(item_name, description, vendor_category):
    """Classify item into shopping category (Level 1) with confidence"""
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


# ======================================================= #
@app.route('/get_shopping_category', methods=['POST'])
def get_shopping_category():
    """
    Process CSV file with shopping category classification

    Expects JSON with:
    - csv_path: path to input CSV file
    - output_path: path to save output CSV file (optional)
    """
    try:
        data = request.get_json()
        csv_path = data.get('csv_path')
        output_path = data.get('output_path', csv_path.replace('.csv', '_shopping_category.csv'))

        if not csv_path:
            return jsonify({"error": "csv_path is required"}), 400

        if not os.path.exists(csv_path):
            return jsonify({"error": f"File not found: {csv_path}"}), 404

        # Read CSV
        df = pd.read_csv(csv_path)

        # Clean column names if needed
        if df.iloc[0].equals(df.columns):
            df.columns = df.iloc[0]
            df = df.drop([0, 1]).reset_index(drop=True)

        # Apply classification
        results = df.apply(
            lambda row: pd.Series(classify_shopping_category(
                row.get("Item (EN)", ""),
                row.get("Description (EN)", ""),
                row.get("Category/Department (EN)", "")
            )),
            axis=1
        )
        df[["shoppingCategory", "confidence"]] = results

        # Save output
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        return jsonify({
            "success": True,
            "message": "Shopping category classification completed",
            "output_path": output_path,
            "processed_rows": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Shopping Category Classification API"})


if __name__ == '__main__':
    print("Starting Shopping Category Classification API...")
    print("API will be available at http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
