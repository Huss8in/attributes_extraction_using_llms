"""
Flask API #10: DSW (Description Search Words) Generation
Generates strict description search words (DSW) for items
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


def generate_dsw(item_name, description, item_category):
    """Generate strict and structured Description Search Words (DSW) for an item"""
    
    prompt = f"""
You are a strict e-commerce keyword phrase generator.

Create 3 to 10 search keyword phrases based on the following rules:

Step One: Generate basic and simple search phrases customers would type when shopping for the item online.
To do Step One, define:
--Search keyword phrases = adjective-noun pairings
--Adjectives = attributes
--Attributes = modifiers
--Modifiers = functional, tangible or physical features and/or proper nouns (names or brands)
--Nouns = item names
--Search Keyword Format = modifier + modifier + noun

Step Two: Eliminate Unnecessary Adjectives, Numbers and/or Symbols.
To do Step Two, recognize as unnecessary:
--All sentiments, opinions, qualitative or subjective adjectives
--All non-words, acronyms, abbreviations, numbers, dates, model numbers, or symbols

Step Three: Limit each phrase to be no longer than three tokens.
To do Step Three, use this formula:
Search Keyword Phrase = modifier + modifier + noun

Additional Rules:
1. Each phrase must end with the main product noun from the item name (not the category).
2. Include exactly one phrase that is only the product noun itself.
3. Use only meaningful tangible attributes from the description.
4. Avoid repetition and unnecessary filler phrases.
5. Output between 3 and 10 phrases depending on relevance.
6. Phrases must be separated by commas, with no numbering, bullets, or extra text.

Generate the search keyword phrases from this data below:

Item Name: {item_name}
Description: {description}
Item Category: {item_category}

Output ONLY the keyword phrases, comma-separated, no extra text:
"""

    result = run_model(prompt)
    # Normalize output cleanly
    result = result.replace("\n", "").replace('"', "").replace("'", "").strip().lower()
    print(f"MODEL RAW RESULT: {result}")
    return result



@app.route('/get_dsw', methods=['POST'])
def get_dsw():
    """
    Process CSV for DSW generation.
    Input JSON:
    {
        "csv_path": "path/to/input.csv",
        "output_path": "optional/output.csv"
    }
    """
    try:
        data = request.get_json()
        csv_path = data.get("csv_path")
        output_path = data.get("output_path", csv_path.replace(".csv", "_dsw.csv"))

        if not csv_path:
            return jsonify({"error": "csv_path is required"}), 400
        if not os.path.exists(csv_path):
            return jsonify({"error": f"File not found: {csv_path}"}), 404

        df = pd.read_csv(csv_path)

        # Fix duplicated headers
        if df.iloc[0].equals(df.columns):
            df.columns = df.iloc[0]
            df = df.drop([0, 1]).reset_index(drop=True)

        # Generate DSW
        df["DSW"] = df.apply(
            lambda row: generate_dsw(
                row.get("Item (EN)", ""),
                row.get("Description (EN)", ""),
                row.get("itemCategory", "")  # <-- use Level 3 category
            ),
            axis=1
        )

        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return jsonify({
            "success": True,
            "message": "DSW generation completed successfully",
            "output_path": output_path,
            "processed_rows": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "DSW Generation API"})


if __name__ == '__main__':
    print("Starting DSW Generation API...")
    print("API will be available at http://localhost:5006/get_dsw")
    app.run(debug=True, host='0.0.0.0', port=5006)
