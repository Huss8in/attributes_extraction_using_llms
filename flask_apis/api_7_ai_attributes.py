"""
Flask API #11: AI-Attributes Extraction (Strict)
Extracts detailed product attributes from item information
"""

from flask import Flask, request, jsonify
import pandas as pd
import requests
import os

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


@app.route('/get_ai_attributes', methods=['POST'])
def get_ai_attributes():
    """
    Process CSV for AI attributes extraction.
    Input JSON:
    {
        "csv_path": "path/to/input.csv",
        "output_path": "optional/output.csv"
    }
    """
    try:
        data = request.get_json()
        csv_path = data.get("csv_path")
        output_path = data.get("output_path", csv_path.replace(".csv", "_ai_attributes.csv"))

        if not csv_path:
            return jsonify({"error": "csv_path is required"}), 400
        if not os.path.exists(csv_path):
            return jsonify({"error": f"File not found: {csv_path}"}), 404

        df = pd.read_csv(csv_path)

        # Fix duplicated headers
        if df.iloc[0].equals(df.columns):
            df.columns = df.iloc[0]
            df = df.drop([0, 1]).reset_index(drop=True)

        # Extract AI attributes
        df["AI_Attributes"] = df.apply(
            lambda row: extract_ai_attributes(
                row.get("Item (EN)", ""),
                row.get("Description (EN)", ""),
                row.get("Category/Department (EN)", ""),
                row.get("shoppingCategory", ""),
                row.get("shoppingSubcategory", ""),
                row.get("itemCategory", "")
            ),
            axis=1
        )

        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return jsonify({
            "success": True,
            "message": "AI attributes extraction completed successfully",
            "output_path": output_path,
            "processed_rows": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "AI Attributes Extraction API"})


if __name__ == '__main__':
    print("Starting AI Attributes Extraction API...")
    print("API will be available at http://localhost:5007/get_ai_attributes")
    app.run(debug=True, host='0.0.0.0', port=5007)
