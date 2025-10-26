"""
JSON API #6: DSW (Description Search Words) Generation
Accepts JSON input and returns DSW as string
"""

from flask import Flask, request, jsonify
import requests

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

# ---------------------------------------------------------------------- #
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


# ---------------------------------------------------------------------- #

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()

        item_name = data.get('item_name', '')
        description = data.get('description', '')
        item_category = data.get('item_category', '')

        if not item_category:
            return jsonify({"error": "item_category is required"}), 400

        dsw = generate_dsw(item_name, description, item_category)

        return jsonify({"dsw": dsw})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON DSW Generation API"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON DSW Generation API",
        "version": "1.0.0",
        "endpoints": {
            "/generate": "Generate DSW for item (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON DSW Generation API")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /generate - Generate DSW for item")
    print("  GET  /health   - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6006")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6006)
