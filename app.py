from flask import Flask, request, jsonify, send_file
import pandas as pd
import requests
import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
OLLAMA_LOCAL_URL = os.getenv("Ollama_URL", "http://127.0.0.1:11434/v1/completions")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ========================
# LLM Functions
# ========================

def ollama_local(prompt):
    """Call local Ollama API"""
    try:
        payload = {
            "model": "llama3.1:8b",
            "prompt": prompt,
            "max_tokens": 200,
            "stream": False
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(OLLAMA_LOCAL_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["text"].strip()
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return ""

def chatgpt(prompt, model="gpt-3.5-turbo"):
    """Call OpenAI ChatGPT API"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling ChatGPT: {e}")
        return ""

# ========================
# Level 1: Shopping Categories
# ========================

shopping_categories = [
    "stationary", "restaurants", "electronics", "pharmacies", "pet care", "home and garden",
    "beauty", "entertainment", "health and nutrition", "groceries", "fashion",
    "automotive", "sports", "kids", "flowers and gifts"
]

# ========================
# Level 2: Shopping Subcategories
# ========================

fashion_subcategories = ["baby clothes", "undergarments", "accessories", "casual wear", "home decor", "beach wear", "outerwear", "neckwear and scarf", "formal wear", "sports wear", "swimwear", "designer wear", "sports", "outdoor sports", "footwear", "martial arts", "sleepwear", "medical wear", "kids wear", "jewelry", "religious wear", "fitness and training", "maternity", "water sports", "eyewear"]
beauty_subcategories = ["skincare", "haircare", "fragrances", "cosmetics"]
home_subcategories = ["drinkware", "home decor", "hardware and home improvement", "tableware", "lighting", "kitchenwear", "gardening and outdoor", "bakeware", "outdoor sports", "household products", "storage and organization", "appliances", "home essentials", "bed and bath", "fitness and training", "furniture", "kitchenware"]
stationary_subcategory = ["office supplies", "stationary", "stationary supplies", "arts and crafts", "school supplies", "stationary accessories"]
restaurants_subcategory = ["desserts", "mexican", "pizza", "specialty foods", "egyptian", "burgers", "korean", "fast food", "street food", "restaurants", "japanese", "italian", "cafes", "mediterranean", "vegan", "salads", "asian", "vietnamese", "lebanese", "international", "pasta", "chinese", "bakery and cakes", "french", "juices & drinks", "thai", "sandwiches", "seafood", "sushi", "keto", "grills", "healthy", "vegetarian", "indian", "american", "middle eastern", "juices and drinks"]
pharmacies_subcategory = ["sportswear", "specialty foods", "first aid and medical equipment", "haircare", "dietary supplements", "men's care", "vitamins", "skincare", "women's deodorant", "medicine", "eye care", "dental care", "incontinence", "women's care"]
pet_care_subcategory = ["aquatic animals", "horses", "dogs", "birds", "small pet supplies", "cats"]
sports_subcategory = ["outdoor sports", "sports", "footwear", "team sports", "winter sports", "recreational activities", "swimwear", "fitness and training", "accessories", "water sports", "martial arts", "sportswear"]
entertainment_subcategory = ["books", "gaming", "music", "musical instruments", "toys and games", "musical equipment"]
health_and_nutrition_subcategory = ["natural solutions", "weight management", "specialty foods", "men's care", "performance supplements", "protein products", "vitamins", "dietary supplements"]
groceries_subcategory = ["salads", "supermarkets", "specialty foods", "mini marts", "bakery and cakes", "desserts", "cafes"]
automotive_subcategory = ["auto accessories", "motorcycle care"]
kids_subcategory = ["baby safety products", "baby care", "baby furniture", "kids furniture", "baby travel", "baby clothes", "swimwear", "kids furniture accessory", "toys and games"]
flowers_and_gifts_subcategory = ["flowers", "gifts"]

subcategory_map = {
    "fashion": fashion_subcategories,
    "beauty": beauty_subcategories,
    "home and garden": home_subcategories,
    "stationary": stationary_subcategory,
    "restaurants": restaurants_subcategory,
    "pharmacies": pharmacies_subcategory,
    "pet care": pet_care_subcategory,
    "sports": sports_subcategory,
    "entertainment": entertainment_subcategory,
    "health and nutrition": health_and_nutrition_subcategory,
    "groceries": groceries_subcategory,
    "gifts and flowers": flowers_and_gifts_subcategory,
    "automotive": automotive_subcategory,
    "kids": kids_subcategory,
    "flowers and gifts": flowers_and_gifts_subcategory
}

# ========================
# Level 3: Item Categories
# ========================

fashion_item_categories = {
    "baby clothes": ["onesie", "diaper shirt", "babygrow", "lap tee", "romper", "baby shoe", "jumpsuit", "baby sock", "baby gown", "baby mitten", "diaper cover", "baby leggings", "bloomers", "baby accessory"],
    "undergarments": ["undershirt", "nightgown", "bra", "camisole", "panty", "baby doll", "boxers", "slip", "briefs", "corset"],
    "accessories": ["belt", "bag", "headwear", "hair accessories", "glove", "umbrella", "wallet", "luggage", "briefcase", "trunk", "laptopcase", "hand fan", "watch"],
    "casual wear": ["apron", "top", "trousers", "blouse", "t-shirt", "shirt", "vest", "pants", "shorts", "leggings", "skirt", "dress", "outfit", "skort"],
    "beach wear": ["bathing cover"],
    "outerwear": ["sweatshirt", "sweater", "tank top", "jacket", "coat", "overalls", "jeans", "kimono"],
    "neckwear and scarf": ["tie", "shawl", "ascot", "pashmina", "boa", "scarf", "handkerchief", "bandana"],
    "formal wear": ["blazer", "suit", "uniform", "rope"],
    "sports wear": ["sportswear"],
    "swimwear": ["swimsuit"],
    "footwear": ["sandals", "slippers", "boot", "sports shoe", "shoe", "stocking", "sock", "shoe accessory"],
    "sleepwear": ["pajamas"],
    "jewelry": ["earrings", "necklace", "bracelet", "broche", "pendant", "cufflink", "head ornament", "jewelry box", "ring", "jewelry set", "tie pin"],
    "religious wear": ["islamic religious wear", "christian religious wear"],
    "maternity": ["maternity"],
    "eyewear": ["glasses", "sunglasses"]
}

beauty_item_categories = {
    "skincare": ["foot care", "hand care", "loofah and sponge", "cotton", "hair removal", "face treatment", "anti-aging", "eye treatment", "acne", "skin whitening", "dark spot", "sunscreen", "face soap", "face scrub", "face toner", "face moisturizer", "face cleanser", "face mask", "hand soap", "body scrub", "bath soap", "bath salt", "bath cream", "shower gel", "body moisturizer", "body oil", "face roller", "skincare accessory", "injectables", "skincare set"],
    "haircare": ["hair gel", "hair brush and comb", "hair mousse", "hair styling tool", "hair wax", "hair dye", "hair spray", "hair loss", "hair cream", "hair shampoo", "hair conditioner", "hair oil", "hair mask", "hair serum", "haircare set", "hair treatment"],
    "fragrances": ["body spray", "cologne", "perfume"],
    "cosmetics": ["eye make-up", "lip make-up", "face make-up", "nailcare", "cosmetics accessory", "make-up tool", "body make-up", "cosmetic set"]
}

home_item_categories = {
    "drinkware": ["cup", "glass", "mug", "wine glass", "champagne flute", "martini glass", "beer glass", "sake cup", "sherry glass", "shot glass", "cognac glass", "margarira glass", "brandy glass", "whisky glass", "rummer", "tumbler", "teacup", "beaker", "coaster", "pitcher", "carafe", "jar", "wine opener", "flask", "trembleuse", "straw", "drinkware accessory"],
    "home decor": ["wallpaper", "clock", "candle", "vase", "tapestery", "wall art", "picture frame", "decorative plate", "home scent", "incense", "mirror", "potpurri", "home decor accessory"],
    "hardware and home improvement": ["home tool", "measuring tool", "plumbing tool", "electrical tool", "power tool", "hand tool", "welding", "duct tape", "cord", "flashlight", "nail and screw", "fastener and snap", "padlock", "shelf support", "window hardware", "home automation device"],
    "tableware": ["cutlery", "plate and bowl", "table linen"],
    "lighting": ["wall lighting", "lamp", "chandlier", "light bulb", "underwater lighting", "lighting accessory", "ceiling lighting", "floor lighting", "outdoor lighting", "lighting system"],
    "kitchenwear": ["cooking utensil", "cooking tool", "speciality cookwear", "ovenware", "pot and pan", "kitchen accessory"],
    "gardening and outdoor": ["gardening tool", "gardening equipment", "gardening care", "pool equipment"],
    "bakeware": ["baking pan", "bakeware utensil", "bakeware accessory"],
    "household products": ["cleaning tool", "cleaning products", "house supply"],
    "storage and organization": ["office storage and organization", "clothing storage and organization", "bathroom storage and organization", "bedroom storage and organization", "kitchen storage and organization", "outdoor storage and organization", "kids storage and organization", "garage storage and organization"],
    "appliances": ["personal appliances", "kitchen appliance", "home appliance", "heating and cooling unit", "cleaning appliance", "specialty appliance"],
    "bed and bath": ["bath linen", "bath accessory", "bathroom hardware", "bedding"],
    "furniture": ["bedroom furniture", "kitchen furniture", "bathroom furniture", "dining room furniture", "living room furniture", "office furniture", "outdoor furniture", "furniture accessory", "kids furniture"],
    "kitchenware": ["french press", "percolator", "coffee pot", "tea pot", "tea strainer", "cookware set", "double boiler", "braiser", "saucier"]
}

stationary_item_categories = {
    "office supplies": ["scissors", "sharpener", "desk organizer", "paper puncher", "notebook", "chalk board", "desk planner", "white board", "writing pad", "chalk", "stapler", "calendar", "sticky note", "folder", "crayon", "tack", "agenda", "sheet protector", "clip board", "photo album", "cork board", "office supply accessories"],
    "stationary": ["stationary"],
    "stationary supplies": ["document holder", "tape", "eraser", "glue", "pencil", "pen", "paper clip", "marker", "compass", "book cover", "bookmark", "ruler"],
    "arts and crafts": ["craft supply", "knitting", "sewing", "jewelry making", "painting", "drawing", "pottery", "sculpting", "basket making", "candle making", "doll making", "craft fabric", "floral arranging", "weaving", "print making", "arts and crafts set"],
    "school supplies": ["notebook", "writing pad", "chalk board", "chalk", "folder", "crayon", "pencil case", "clip board", "pencil holder", "cork board", "book cover", "bookmark", "school supply accessories", "ruler"],
    "stationary accessories": ["keychain", "pencil case", "pencil holder"]
}

category_item_map = {
    "fashion": fashion_item_categories,
    "beauty": beauty_item_categories,
    "home and garden": home_item_categories,
    "stationary": stationary_item_categories
}

# ========================
# Classification Functions
# ========================

def classify_shopping_category(item_name, description, vendor_category):
    """Classify item into shopping category (Level 1)"""
    text = f"""
    Item: {item_name}
    Description: {description}
    Vendor Category: {vendor_category}

    Task: Choose the best suited shopping category for this item.

    Allowed categories:
    {shopping_categories}

    Rules:
    - Return ONLY one category name exactly as written in the list
    - If none fit, return nothing
    - Do not add quotes, punctuation, or explanations
    """
    result = ollama_local(text).strip()
    result = result.lower().replace("'", "").replace('"', "").replace(":", "").strip()

    if result not in shopping_categories:
        return ""
    return result

def classify_shopping_subcategory(item_name, description, vendor_category, main_cat):
    """Classify item into shopping subcategory (Level 2)"""
    if not main_cat or main_cat not in subcategory_map:
        return ""

    allowed_subcats = subcategory_map[main_cat]

    text = f"""
    Item: {item_name}
    Description: {description}
    Vendor Category: {vendor_category}
    Main Category: {main_cat}

    Task: Choose the best suited subcategory for this item.

    Allowed subcategories:
    {allowed_subcats}

    Rules:
    - Return ONLY one subcategory name exactly as written in the list
    - If none fit, return nothing
    - Do not add quotes, punctuation, or explanations
    """

    result = ollama_local(text).strip().lower()
    result = result.replace("'", "").replace('"', "").replace(":", "").strip()

    if result not in allowed_subcats:
        return ""
    return result

def classify_item_category(item_name, description, vendor_category, main_cat, sub_cat):
    """Classify item into item category (Level 3)"""
    if not main_cat or main_cat not in category_item_map:
        return ""

    if not sub_cat or sub_cat not in category_item_map[main_cat]:
        return ""

    allowed_items = category_item_map[main_cat][sub_cat]

    text = f"""
    Item: {item_name}
    Description: {description}
    Vendor Category: {vendor_category}
    Main Category: {main_cat}
    Subcategory: {sub_cat}

    Task: Choose the best suited item category for this item.

    Allowed item categories:
    {allowed_items}

    Rules:
    - Return ONLY one item category name exactly as written in the list
    - If none fit, return nothing
    - Do not add quotes, punctuation, or explanations
    """

    result = ollama_local(text).strip().lower()
    result = result.replace("'", "").replace('"', "").replace(":", "").strip()

    if result not in allowed_items:
        return ""
    return result

# ========================
# SKW, DSW, and AI Attributes Functions
# ========================

def generate_skw(item_name, vendor_category):
    """Generate Search Keywords (SKW)"""
    skw_input = f"Item name: {item_name}\nVendor Category: {vendor_category}"

    skw_prompt = (
        """Generate 5 shopping keyword phrases for this item.
Rules:
- Do not use numbering or extra text, only list the phrases.
- The first phrase must be only the product category (example: "Ring", "Necklace", etc.).
- All other phrases must end with the product category word.
- Each phrase must be maximum 3 words only. Never exceed 3 words.
- Format = modifier + modifier + product category.
- Modifiers = tangible features or proper nouns.
- Remove sentiments, numbers, dates, symbols.
Item data: """
        + skw_input
    )

    return chatgpt(skw_prompt)

def generate_dsw(item_name, vendor_category):
    """Generate Description Search Words (DSW)"""
    dsw_input = f"Item name: {item_name}\nVendor Category: {vendor_category}"

    dsw_prompt = (
        """Generate 5–10 shopping keyword phrases for this item.
Rules:
- Do not use numbering, bullets, or extra comments, only list the phrases.
- Each phrase must end with the main product word.
- Format (≤3 words) = modifier + modifier + main product.
- Modifiers = tangible features, functional attributes, or proper nouns.
- Include exactly one phrase with only the main product (example: "Ring").
- Remove sentiments, opinions, numbers, dates, symbols, and abbreviations.
Item data: """
        + dsw_input
    )

    return ollama_local(dsw_prompt)

def generate_ai_attributes(item_name, vendor_category, item_category):
    """Generate AI Attributes (gender, color, etc.)"""
    ai_input = f"Item name: {item_name}\nVendor Category: {vendor_category}\nItem Category: {item_category}"

    ai_prompt = (
        f"Item data: {ai_input}"
        + """
- Identify all attributes of this item. Only fill attributes that can be clearly inferred from the data; leave unknowns empty. Do not include extra statements, explanations, or brackets. Use short, precise values in English.

- Gender must be chosen strictly from this list only:
  ["Women", "Men", "Unisex women, Unisex men", "Girls", "Boys", "Unisex girls, unisex boys"].
  Do not invent or shorten values (e.g., "Unisex men" is invalid).

- Generic Name should use the item category if possible.
- Color should be inferred from the item name or category if present.
- Product Name should be concise and represent the product, not copied verbatim.

Format exactly as:

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
"""
    )

    return chatgpt(ai_prompt)

# ========================
# Main Processing Function
# ========================

def process_row(row):
    """Process a single row and generate all classifications and attributes"""
    item_name = row.get("Item (EN)", "")
    description = row.get("Description (EN)", "")
    vendor_category = row.get("Category/Department (EN)", "")

    # Level 1: Shopping Category
    shopping_category = classify_shopping_category(item_name, description, vendor_category)
    if not shopping_category:
        shopping_category = "template"

    # Level 2: Shopping Subcategory
    shopping_subcategory = classify_shopping_subcategory(item_name, description, vendor_category, shopping_category)
    if not shopping_subcategory:
        shopping_subcategory = "template"

    # Level 3: Item Category
    item_category = classify_item_category(item_name, description, vendor_category, shopping_category, shopping_subcategory)
    if not item_category:
        item_category = "template"

    # Generate SKW, DSW, and AI Attributes
    skw = generate_skw(item_name, vendor_category)
    dsw = generate_dsw(item_name, vendor_category)
    ai_attributes = generate_ai_attributes(item_name, vendor_category, item_category)

    return {
        "shopping_category": shopping_category,
        "shopping_subcategory": shopping_subcategory,
        "item_category": item_category,
        "skw": skw,
        "dsw": dsw,
        "ai_attributes": ai_attributes
    }

# ========================
# Flask Endpoints
# ========================

@app.route('/process', methods=['POST'])
def process_csv():
    """Process CSV file and return enriched data"""
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are supported'}), 400

        # Read CSV
        df = pd.read_csv(file)

        # Clean column names (handle the header row issue)
        df.columns = df.iloc[0]
        df = df.drop([0, 1]).reset_index(drop=True)

        # Keep only needed columns
        needed_columns = ["Item (EN)", "Description (EN)", "Category/Department (EN)", "Variant Name"]
        available_columns = [col for col in needed_columns if col in df.columns]
        df = df[available_columns]

        # Get output format preference (csv or excel)
        output_format = request.form.get('format', 'csv').lower()

        # Process each row
        results = []
        for idx, row in df.iterrows():
            enriched_data = process_row(row)

            # Combine original data with enriched data
            result_row = {
                "Item (EN)": row.get("Item (EN)", ""),
                "Description (EN)": row.get("Description (EN)", ""),
                "Category/Department (EN)": row.get("Category/Department (EN)", ""),
                "Variant Name": row.get("Variant Name", ""),
                "Shopping Category": enriched_data["shopping_category"],
                "Shopping Subcategory": enriched_data["shopping_subcategory"],
                "Item Category": enriched_data["item_category"],
                "SKW": enriched_data["skw"],
                "DSW": enriched_data["dsw"],
                "AI Attributes": enriched_data["ai_attributes"]
            }
            results.append(result_row)

        # Create DataFrame from results
        result_df = pd.DataFrame(results)

        # Generate downloadable file
        output = BytesIO()

        if output_format == 'excel':
            result_df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='enriched_data.xlsx'
            )
        else:  # default to CSV
            result_df.to_csv(output, index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name='enriched_data.csv'
            )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'AI Item Data Generator API is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
