"""
Flask API: Master Pipeline
Applies all 8 APIs sequentially to process a CSV file end-to-end
"""

from flask import Flask, request, jsonify
import pandas as pd
import requests
import os
import sys

# Import mapping files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mapping import shoppingCategory, shoppingSubcategory_map, itemCategory_map, itemSubcategory_map

app = Flask(__name__)

# Model configuration
API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "phi4:latest"
TRANSLATION_MODEL = "aya:8b"


def run_model(prompt, max_tokens=200, model=MODEL_NAME):
    """Run the AI model with the given prompt"""
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "stream": False}
    r = requests.post(API_URL, json=payload)
    r.raise_for_status()
    return r.json()["response"].strip()


# ======================================================= #
# API 1: Shopping Category Classification
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
    print(f"[API 1] Shopping Category: {result}")

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
# API 2: Shopping Subcategory Classification
# ======================================================= #
def classify_shopping_subcategory(shopping_category, item_name, description, vendor_category):
    """Classify item into shopping subcategory (Level 2) with confidence"""

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

    result = run_model(prompt, max_tokens=150)
    result = result.lower().strip().splitlines()[0]
    print(f"[API 2] Shopping Subcategory: {result}")

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


# ======================================================= #
# API 3: Item Category Classification
# ======================================================= #
def classify_item_category(shopping_category, shopping_subcategory, item_name, description, vendor_category):
    """Classify item into item category (Level 3) with strict format"""

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

    result = run_model(prompt, max_tokens=150)
    result = result.lower().replace("'", "").replace('"', "").strip()
    print(f"[API 3] Item Category: {result}")

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


# ======================================================= #
# API 4: Item Subcategory Classification
# ======================================================= #
def classify_item_subcategory(shopping_category, shopping_subcategory, item_category, item_name, description, vendor_category):
    """Classify item into item subcategory (Level 4) with strict format"""

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

    result = run_model(prompt, max_tokens=200)
    result = result.lower().replace("'", "").replace('"', "").strip()
    print(f"[API 4] Item Subcategory: {result}")

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


# ======================================================= #
# API 5: SKW (Search Keywords) Generation
# ======================================================= #
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

    result = run_model(prompt, max_tokens=200)
    print(f"[API 5] SKW: {result}")

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
    return ", ".join([kw.title() for kw in final_keywords])


# ======================================================= #
# API 6: DSW (Description Search Words) Generation
# ======================================================= #
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

    result = run_model(prompt, max_tokens=200)
    # Normalize output cleanly
    result = result.replace("\n", "").replace('"', "").replace("'", "").strip().lower()
    print(f"[API 6] DSW: {result}")
    return result


# ======================================================= #
# API 7: AI-Attributes Extraction
# ======================================================= #
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
- Generic Name: identify the main item (e.g. if "Matelda Chocolate cake 120 grams" → Generic Name: "cake")
- Product Name: the product name without size/quantity (e.g. "Matelda Chocolate cake")
- Color: infer from name or description
- Keep the output clean and structured exactly as below.

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

    result = run_model(prompt, max_tokens=300)
    result = result.replace("\r", "").strip()
    print(f"[API 7] AI Attributes: {result[:100]}...")
    return result


# ======================================================= #
# API 8: Arabic Translation
# ======================================================= #
def translate_to_arabic(text):
    """Translate text from English to Arabic"""
    if not text or text.strip().lower() == "empty":
        return ""

    prompt = (
        "You are a professional English to Arabic translator for e-commerce. "
        "Translate the following text into Arabic. Respond with Arabic text only, no explanations.\n\n"
        + text
    )

    try:
        result = run_model(prompt, max_tokens=200, model=TRANSLATION_MODEL)
        print(f"[API 8] Translation: {text[:50]}... -> {result[:50]}...")
        return result
    except Exception as e:
        print(f"Translation error: {e}")
        return ""


# ======================================================= #
# Master Pipeline Endpoint
# ======================================================= #
@app.route('/process_csv_pipeline', methods=['POST'])
def process_csv_pipeline():
    """
    Process CSV file through all 8 APIs in sequence

    Expects JSON with:
    - csv_path: path to input CSV file
    - output_path: path to save output CSV file (optional)
    - translate_fields: list of fields to translate to Arabic (optional)
    """
    try:
        data = request.get_json()
        csv_path = data.get('csv_path')
        output_path = data.get('output_path', csv_path.replace('.csv', '_processed_full.csv'))
        translate_fields = data.get('translate_fields', [])

        if not csv_path:
            return jsonify({"error": "csv_path is required"}), 400

        if not os.path.exists(csv_path):
            return jsonify({"error": f"File not found: {csv_path}"}), 404

        print(f"\n{'='*60}")
        print(f"Starting Master Pipeline Processing")
        print(f"Input: {csv_path}")
        print(f"Output: {output_path}")
        print(f"{'='*60}\n")

        # Read CSV
        df = pd.read_csv(csv_path)

        # Clean column names if needed
        if df.iloc[0].equals(df.columns):
            df.columns = df.iloc[0]
            df = df.drop([0, 1]).reset_index(drop=True)

        total_rows = len(df)
        print(f"Processing {total_rows} rows...\n")

        # Process each row through all APIs
        for idx, row in df.iterrows():
            print(f"\n--- Processing Row {idx + 1}/{total_rows} ---")

            item_name = row.get("Item (EN)", "")
            description = row.get("Description (EN)", "")
            vendor_category = row.get("Category/Department (EN)", "")

            # API 1: Shopping Category
            shopping_cat, shopping_conf = classify_shopping_category(item_name, description, vendor_category)
            df.at[idx, "shoppingCategory"] = shopping_cat
            df.at[idx, "confidence"] = shopping_conf

            # API 2: Shopping Subcategory
            shopping_subcat, subcat_conf = classify_shopping_subcategory(shopping_cat, item_name, description, vendor_category)
            df.at[idx, "shoppingSubcategory"] = shopping_subcat
            df.at[idx, "subcategory_confidence"] = subcat_conf

            # API 3: Item Category
            item_cat, item_cat_conf = classify_item_category(shopping_cat, shopping_subcat, item_name, description, vendor_category)
            df.at[idx, "itemCategory"] = item_cat
            df.at[idx, "itemCategory_confidence"] = item_cat_conf

            # API 4: Item Subcategory
            item_subcat, item_subcat_conf = classify_item_subcategory(shopping_cat, shopping_subcat, item_cat, item_name, description, vendor_category)
            df.at[idx, "itemSubcategory"] = item_subcat
            df.at[idx, "itemSubcategory_confidence"] = item_subcat_conf

            # API 5: SKW Generation
            skw = generate_skw(item_name, item_cat)
            df.at[idx, "SKW"] = skw

            # API 6: DSW Generation
            dsw = generate_dsw(item_name, description, item_cat)
            df.at[idx, "DSW"] = dsw

            # API 7: AI Attributes
            ai_attrs = extract_ai_attributes(item_name, description, vendor_category, shopping_cat, shopping_subcat, item_cat)
            df.at[idx, "AI_Attributes"] = ai_attrs

            # API 8: Arabic Translation (if specified)
            if translate_fields:
                for field in translate_fields:
                    if field in df.columns:
                        text_to_translate = str(row.get(field, ""))
                        if text_to_translate:
                            translated = translate_to_arabic(text_to_translate)
                            df.at[idx, f"{field}_AR"] = translated

            print(f"Row {idx + 1} completed successfully")

        # Save output
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"\n{'='*60}")
        print(f"Pipeline Processing Completed!")
        print(f"Output saved to: {output_path}")
        print(f"{'='*60}\n")

        return jsonify({
            "success": True,
            "message": "Full pipeline processing completed successfully",
            "output_path": output_path,
            "processed_rows": len(df),
            "columns_added": [
                "shoppingCategory", "confidence",
                "shoppingSubcategory", "subcategory_confidence",
                "itemCategory", "itemCategory_confidence",
                "itemSubcategory", "itemSubcategory_confidence",
                "SKW", "DSW", "AI_Attributes"
            ] + [f"{f}_AR" for f in translate_fields]
        })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_trace}")
        return jsonify({"error": str(e), "traceback": error_trace}), 500


@app.route('/process_folder', methods=['POST'])
def process_folder():
    """
    Process all CSV files in a folder through the pipeline

    Expects JSON with:
    - folder_path: path to folder containing CSV files
    - output_folder: path to save processed CSV files (optional)
    - translate_fields: list of fields to translate to Arabic (optional)
    - file_pattern: glob pattern for CSV files (default: *.csv)
    """
    try:
        import glob
        from datetime import datetime

        data = request.get_json()
        folder_path = data.get('folder_path')
        output_folder = data.get('output_folder', os.path.join(folder_path, 'processed'))
        translate_fields = data.get('translate_fields', [])
        file_pattern = data.get('file_pattern', '*.csv')

        if not folder_path:
            return jsonify({"error": "folder_path is required"}), 400

        if not os.path.exists(folder_path):
            return jsonify({"error": f"Folder not found: {folder_path}"}), 404

        # Create output folder
        os.makedirs(output_folder, exist_ok=True)

        # Find all CSV files
        search_pattern = os.path.join(folder_path, file_pattern)
        csv_files = glob.glob(search_pattern)

        if not csv_files:
            return jsonify({"error": f"No CSV files found matching pattern: {file_pattern}"}), 404

        print(f"\n{'='*60}")
        print(f"Batch Processing {len(csv_files)} CSV files")
        print(f"Folder: {folder_path}")
        print(f"Output: {output_folder}")
        print(f"{'='*60}\n")

        results = []
        start_time = datetime.now()

        for idx, csv_file in enumerate(csv_files, 1):
            filename = os.path.basename(csv_file)
            print(f"\n[{idx}/{len(csv_files)}] Processing: {filename}")

            try:
                # Read CSV
                df = pd.read_csv(csv_file)

                # Clean column names if needed
                if df.iloc[0].equals(df.columns):
                    df.columns = df.iloc[0]
                    df = df.drop([0, 1]).reset_index(drop=True)

                # Process each row
                for row_idx, row in df.iterrows():
                    item_name = row.get("Item (EN)", "")
                    description = row.get("Description (EN)", "")
                    vendor_category = row.get("Category/Department (EN)", "")

                    # API 1: Shopping Category
                    shopping_cat, shopping_conf = classify_shopping_category(item_name, description, vendor_category)
                    df.at[row_idx, "shoppingCategory"] = shopping_cat
                    df.at[row_idx, "confidence"] = shopping_conf

                    # API 2: Shopping Subcategory
                    shopping_subcat, subcat_conf = classify_shopping_subcategory(shopping_cat, item_name, description, vendor_category)
                    df.at[row_idx, "shoppingSubcategory"] = shopping_subcat
                    df.at[row_idx, "subcategory_confidence"] = subcat_conf

                    # API 3: Item Category
                    item_cat, item_cat_conf = classify_item_category(shopping_cat, shopping_subcat, item_name, description, vendor_category)
                    df.at[row_idx, "itemCategory"] = item_cat
                    df.at[row_idx, "itemCategory_confidence"] = item_cat_conf

                    # API 4: Item Subcategory
                    item_subcat, item_subcat_conf = classify_item_subcategory(shopping_cat, shopping_subcat, item_cat, item_name, description, vendor_category)
                    df.at[row_idx, "itemSubcategory"] = item_subcat
                    df.at[row_idx, "itemSubcategory_confidence"] = item_subcat_conf

                    # API 5: SKW Generation
                    skw = generate_skw(item_name, item_cat)
                    df.at[row_idx, "SKW"] = skw

                    # API 6: DSW Generation
                    dsw = generate_dsw(item_name, description, item_cat)
                    df.at[row_idx, "DSW"] = dsw

                    # API 7: AI Attributes
                    ai_attrs = extract_ai_attributes(item_name, description, vendor_category, shopping_cat, shopping_subcat, item_cat)
                    df.at[row_idx, "AI_Attributes"] = ai_attrs

                    # API 8: Arabic Translation (if specified)
                    if translate_fields:
                        for field in translate_fields:
                            if field in df.columns:
                                text_to_translate = str(row.get(field, ""))
                                if text_to_translate:
                                    translated = translate_to_arabic(text_to_translate)
                                    df.at[row_idx, f"{field}_AR"] = translated

                # Save output
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(output_folder, f"{base_name}_processed.csv")
                df.to_csv(output_path, index=False, encoding='utf-8-sig')

                results.append({
                    "success": True,
                    "input_file": csv_file,
                    "output_file": output_path,
                    "rows_processed": len(df)
                })

                print(f"  ✓ Completed: {filename} ({len(df)} rows)")

            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"  ✗ Failed: {filename} - {str(e)}")
                results.append({
                    "success": False,
                    "input_file": csv_file,
                    "error": str(e),
                    "traceback": error_trace
                })

        end_time = datetime.now()
        duration = str(end_time - start_time)

        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful

        print(f"\n{'='*60}")
        print(f"Batch Processing Completed!")
        print(f"Total: {len(results)} | Success: {successful} | Failed: {failed}")
        print(f"Duration: {duration}")
        print(f"{'='*60}\n")

        return jsonify({
            "success": True,
            "message": "Batch processing completed",
            "total_files": len(csv_files),
            "successful": successful,
            "failed": failed,
            "duration": duration,
            "output_folder": output_folder,
            "results": results
        })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_trace}")
        return jsonify({"error": str(e), "traceback": error_trace}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Master Pipeline API",
        "apis_included": [
            "API 1: Shopping Category",
            "API 2: Shopping Subcategory",
            "API 3: Item Category",
            "API 4: Item Subcategory",
            "API 5: SKW Generation",
            "API 6: DSW Generation",
            "API 7: AI Attributes",
            "API 8: Arabic Translation"
        ]
    })


if __name__ == '__main__':
    print("="*60)
    print("Starting Master Pipeline API...")
    print("This API chains all 8 APIs together:")
    print("  1. Shopping Category Classification")
    print("  2. Shopping Subcategory Classification")
    print("  3. Item Category Classification")
    print("  4. Item Subcategory Classification")
    print("  5. SKW Generation")
    print("  6. DSW Generation")
    print("  7. AI Attributes Extraction")
    print("  8. Arabic Translation")
    print("="*60)
    print("\nAPI will be available at http://localhost:5000/process_csv_pipeline")
    print("\nUsage:")
    print('  POST {"csv_path": "path/to/file.csv"}')
    print('  Optional: {"output_path": "path/to/output.csv"}')
    print('  Optional: {"translate_fields": ["Item (EN)", "Description (EN)"]}')
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)
