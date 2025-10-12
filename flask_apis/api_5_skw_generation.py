"""
Flask API #9: SKW (Search Keywords) Generation
Generates strict search keywords (SKW) for items
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
    payload = {"model": MODEL_NAME, "prompt": prompt, "max_tokens": 200, "stream": False}
    r = requests.post(API_URL, json=payload)
    r.raise_for_status()
    return r.json()["response"].strip()


def generate_skw(item_name, description, item_category):
    """Generate strict Search Keywords (SKW) for an item using the item_category from CSV"""

    input_text = f"Item: {item_name}\nDescription: {description}\nItem Category: {item_category}"

    prompt = f"""
You are a strict e-commerce keyword generator.
Generate exactly 5 keyword phrases for the item below. FOLLOW THESE RULES STRICTLY:

Item Data:
{input_text}

Rules:
1. Output exactly 5 phrases separated by commas, no numbering or extra text
2. The first phrase must be ONLY the item category: {item_category}
3. All other phrases must end with the item category: {item_category}
4. Each phrase must be maximum 3 words
5. Format: modifier + modifier + item category
6. Use tangible features, proper nouns, or item attributes as modifiers
7. Do NOT include sentiments, numbers, dates, symbols, or extra words
8. Return everything in lowercase
9. STRICTLY follow the format. Do not add explanations or newlines

Output ONLY:
"""

    result = run_model(prompt)
    result = result.replace("\n", "").replace('"', "").replace("'", "").strip().lower()
    print(f"MODEL RAW RESULT: {result}")
    return result



@app.route('/get_skw', methods=['POST'])
def get_skw():
    """
    Process CSV for SKW generation.
    Input JSON:
    {
        "csv_path": "path/to/input.csv",
        "output_path": "optional/output.csv"
    }
    """
    try:
        data = request.get_json()
        csv_path = data.get("csv_path")
        output_path = data.get("output_path", csv_path.replace(".csv", "_skw.csv"))

        if not csv_path:
            return jsonify({"error": "csv_path is required"}), 400
        if not os.path.exists(csv_path):
            return jsonify({"error": f"File not found: {csv_path}"}), 404

        df = pd.read_csv(csv_path)

        # Fix duplicated headers
        if df.iloc[0].equals(df.columns):
            df.columns = df.iloc[0]
            df = df.drop([0, 1]).reset_index(drop=True)

        # Generate SKW
        df["SKW"] = df.apply(
            lambda row: generate_skw(
                row.get("Item (EN)", ""),
                row.get("Description (EN)", ""),
                row.get("itemCategory", "")# <-- use the Level 3 category
            ),
            axis=1
        )

        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return jsonify({
            "success": True,
            "message": "SKW generation completed successfully",
            "output_path": output_path,
            "processed_rows": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "SKW Generation API"})


if __name__ == '__main__':
    print("Starting SKW Generation API...")
    print("API will be available at http://localhost:5005/get_skw")
    app.run(debug=True, host='0.0.0.0', port=5005)
