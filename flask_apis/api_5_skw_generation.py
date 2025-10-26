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


def generate_skw(item_name, item_category):
    """Fast and accurate SKW generator ensuring core product noun first"""

    prompt = f"""
You are a strict e-commerce keyword generator.
Generate concise keyword phrases (1 to 5 only) that customers would type when shopping for an item online.
Use ONLY the item name and category to decide what keywords make sense.

Item Name: {item_name}
Item Category: {item_category}

Rules:
- Each keyword phrase must contain the core product noun (like pants, top, jacket, dress, etc.).
- The first keyword phrase MUST be only the core product noun.
- Avoid adjectives or promotional words unless part of the item name.
- Each phrase should be short (max 3 words).
- Output 1 to 5 keyword phrases, comma-separated, in Title Case.
- Output ONLY the keyword phrases.
"""

    result = run_model(prompt)
    print("*************************")
    print(result)
    print("*************************")

    # Normalize and split
    result = result.replace("\n", "").replace('"', "").replace("'", "").strip().lower()
    keywords = [k.strip() for k in result.split(",") if k.strip()]

    # Identify the main product noun (last word of item name)
    product_noun = item_name.lower().replace("-", " ").split()[-1]

    # Filter to include only phrases that contain the noun
    keywords = [kw for kw in keywords if product_noun in kw]

    # Always ensure noun is first
    if not keywords or keywords[0] != product_noun:
        keywords = [product_noun] + [kw for kw in keywords if kw != product_noun]

    # Remove duplicates while preserving order, limit to 5
    seen = set()
    final_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            final_keywords.append(kw)
        if len(final_keywords) == 5:
            break

    # Return formatted string
    final_result = ", ".join([kw.title() for kw in final_keywords])
    print(f"MODEL RAW RESULT: {final_result}")
    return final_result



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
