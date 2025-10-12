# Flask APIs Documentation

This directory contains 8 independent Flask microservices, each responsible for one level of the AI-powered product data enrichment pipeline.

## Architecture

Each API is a standalone Flask application that:
- Accepts CSV file paths via POST requests
- Processes data using an LLM (Phi-4)
- Returns enriched CSV with new columns
- Runs on a dedicated port (5001-5008)

## APIs Overview

| API | Port | Endpoint | Purpose |
|-----|------|----------|---------|
| API 1 | 5001 | `/get_shopping_category` | Level 1: Shopping Category Classification |
| API 2 | 5002 | `/get_shopping_subcategory` | Level 2: Shopping Subcategory Classification |
| API 3 | 5003 | `/get_item_category` | Level 3: Item Category Classification |
| API 4 | 5004 | `/get_item_subcategory` | Level 4: Item Subcategory Classification |
| API 5 | 5005 | `/get_skw` | Level 5: Search Keywords (SKW) Generation |
| API 6 | 5006 | `/get_dsw` | Level 6: Description Search Words (DSW) Generation |
| API 7 | 5007 | `/get_ai_attributes` | Level 7: AI Attributes Extraction |
| API 8 | 5008 | `/get_arabic_translation` | Level 8: English → Arabic Translation |

## Common Configuration

All APIs use the same LLM configuration:

```python
API_URL = "http://100.75.237.4:11434/api/generate"
MODEL_NAME = "phi4:latest"
```

Update these values in each API file or use environment variables.

## API Details

### Level 1: Shopping Category (Port 5001)

**File:** `api_1_shopping_category.py`

**Endpoint:** `POST /get_shopping_category`

**Function:** Classifies items into 15 broad shopping categories.

**Request:**
```json
{
  "csv_path": "path/to/input.csv",
  "output_path": "path/to/output.csv"  // optional
}
```

**Output Columns Added:**
- `shoppingCategory` - Classified category
- `confidence` - Confidence score (0-100%)

**Categories:**
- stationary, restaurants, electronics, pharmacies, pet care, home and garden
- beauty, entertainment, health and nutrition, groceries, fashion
- automotive, sports, kids, flowers and gifts

**Example:**
```bash
curl -X POST http://localhost:5001/get_shopping_category \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "items.csv"}'
```

---

### Level 2: Shopping Subcategory (Port 5002)

**File:** `api_2_shopping_subcategory.py`

**Endpoint:** `POST /get_shopping_subcategory`

**Function:** Refines Level 1 categories into specific subcategories.

**Requires:** CSV must already have `shoppingCategory` column (from Level 1)

**Output Columns Added:**
- `shoppingSubcategory` - Refined subcategory
- `confidence` - Confidence score

**Example:**
Fashion → casual wear, outerwear, footwear, accessories
Beauty → skincare, haircare, fragrances, cosmetics

---

### Level 3: Item Category (Port 5003)

**File:** `api_3_item_category.py`

**Endpoint:** `POST /get_item_category`

**Function:** AI-selects precise category within the subcategory.

**Requires:** CSV must have `shoppingCategory` and `shoppingSubcategory` columns

**Output Columns Added:**
- `itemCategory` - Precise item category
- `confidence` - Confidence score

**Example:**
Footwear → sandals, slippers, boot, sports shoe, shoe

---

### Level 4: Item Subcategory (Port 5004)

**File:** `api_4_item_subcategory.py`

**Endpoint:** `POST /get_item_subcategory`

**Function:** Most specific classification under itemCategory.

**Requires:** CSV must have `shoppingCategory`, `shoppingSubcategory`, `itemCategory` columns

**Output Columns Added:**
- `itemSubcategory` - Most specific category
- `confidence` - Confidence score

**Example:**
Sports shoe → tennis shoe, cycling shoe, running shoe, basketball shoe

---

### Level 5: SKW Generation (Port 5005)

**File:** `api_5_skw_generation.py`

**Endpoint:** `POST /get_skw`

**Function:** Generates 5 strict search keyword phrases.

**Requires:** CSV must have `itemCategory` column

**Output Columns Added:**
- `SKW` - Comma-separated search keywords

**Rules:**
1. First phrase = main product (itemCategory)
2. Others = modifier + product (max 3 words)
3. Lowercase, no sentiments/numbers/dates
4. Format: `category, modifier category, modifier modifier category`

**Example Output:**
```
running shoe, lightweight running shoe, nike running shoe, breathable running shoe, athletic running shoe
```

---

### Level 6: DSW Generation (Port 5006)

**File:** `api_6_dsw_generation.py`

**Endpoint:** `POST /get_dsw`

**Function:** Generates 5-10 descriptive keyword phrases from item name and description.

**Output Columns Added:**
- `DSW` - Comma-separated descriptive keywords

**Focus:**
- Tangible features (e.g., "wireless", "waterproof")
- Functional attributes (e.g., "noise-cancelling")
- Proper nouns (e.g., brand names, model names)

**Example Output:**
```
bluetooth headphones, over-ear design, active noise cancellation, sony wh-1000xm4, wireless connectivity, 30-hour battery, premium sound quality
```

---

### Level 7: AI Attributes (Port 5007)

**File:** `api_7_ai_attributes.py`

**Endpoint:** `POST /get_ai_attributes`

**Function:** Extracts structured product attributes.

**Requires:** CSV must have all previous level columns

**Output Columns Added:**
- `AI_Attributes` - Multi-line structured attributes

**Extracted Attributes:**
```
Gender: [Women/Men/Unisex/Girls/Boys]
Age: [Adult/Teen/Child/etc.]
Brand: [Brand name if mentioned]
Generic Name: [Usually the item category]
Product Name: [Concise product name]
Size: [S/M/L/XL or dimensions]
Measurements: [Specific dimensions]
Features: [Key features]
Types of Fashion Styles: [Casual/Formal/Sporty/etc.]
Gem Stones: [If jewelry]
Birth Stones: [If jewelry]
Material: [Cotton/Polyester/Leather/etc.]
Color: [Primary color]
Pattern: [Striped/Floral/Solid/etc.]
Occasion: [Wedding/Casual/Sports/etc.]
Activity: [Running/Yoga/Swimming/etc.]
Season: [Summer/Winter/All-season]
Country of origin: [If known]
```

**Rules:**
- Only fill attributes that can be clearly inferred
- Leave unknown attributes empty (no guessing)
- Use concise English values

---

### Level 8: Arabic Translation (Port 5008)

**File:** `api_8_arabic_translation.py`

**Endpoint:** `POST /get_arabic_translation`

**Function:** Translates English columns to Arabic.

**Output Columns Added:**
- `Item (AR)` - Item name in Arabic
- `Description (AR)` - Description in Arabic
- `Category/Department (AR)` - Category in Arabic

**Rules:**
- Professional e-commerce translation
- Arabic only, no extra text or explanations
- Preserves meaning and context

---

## Common Features

### Health Check

All APIs include a health check endpoint:

```bash
GET http://localhost:500X/health
```

Response:
```json
{
  "status": "healthy",
  "service": "API Name"
}
```

### Error Handling

All APIs return consistent error responses:

```json
{
  "error": "Error message description"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad request (missing parameters)
- `404` - File not found
- `500` - Server error

## Running the APIs

### Start Individual API

```bash
python flask_apis/api_1_shopping_category.py
```

### Start All APIs

Create a bash script `start_all_apis.sh`:

```bash
#!/bin/bash
python flask_apis/api_1_shopping_category.py &
python flask_apis/api_2_shopping_subcategory.py &
python flask_apis/api_3_item_category.py &
python flask_apis/api_4_item_subcategory.py &
python flask_apis/api_5_skw_generation.py &
python flask_apis/api_6_dsw_generation.py &
python flask_apis/api_7_ai_attributes.py &
python flask_apis/api_8_arabic_translation.py &
```

Run:
```bash
chmod +x start_all_apis.sh
./start_all_apis.sh
```

## Processing Pipeline

To process a CSV through all 8 levels:

```bash
# Level 1
curl -X POST http://localhost:5001/get_shopping_category \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "input.csv", "output_path": "level1.csv"}'

# Level 2
curl -X POST http://localhost:5002/get_shopping_subcategory \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "level1.csv", "output_path": "level2.csv"}'

# Level 3
curl -X POST http://localhost:5003/get_item_category \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "level2.csv", "output_path": "level3.csv"}'

# Level 4
curl -X POST http://localhost:5004/get_item_subcategory \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "level3.csv", "output_path": "level4.csv"}'

# Level 5
curl -X POST http://localhost:5005/get_skw \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "level4.csv", "output_path": "level5.csv"}'

# Level 6
curl -X POST http://localhost:5006/get_dsw \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "level5.csv", "output_path": "level6.csv"}'

# Level 7
curl -X POST http://localhost:5007/get_ai_attributes \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "level6.csv", "output_path": "level7.csv"}'

# Level 8
curl -X POST http://localhost:5008/get_arabic_translation \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "level7.csv", "output_path": "final.csv"}'
```

## Testing

Test individual APIs:

```bash
# Test API 1
curl -X POST http://localhost:5001/get_shopping_category \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "test_data.csv"}' | jq

# Check health
curl http://localhost:5001/health | jq
```

## Configuration

### Changing LLM Model

Edit each API file:

```python
# Change these values
API_URL = "http://your-llm-server:port/api/generate"
MODEL_NAME = "your-model-name"
```

### Adjusting Max Tokens

Each API has a `max_tokens` parameter in the `run_model()` function:

```python
payload = {
    "model": MODEL_NAME,
    "prompt": prompt,
    "max_tokens": 200,  # Adjust this
    "stream": False
}
```

Recommended values:
- Levels 1-4 (Classification): 100-200 tokens
- Levels 5-6 (Keywords): 150-200 tokens
- Level 7 (Attributes): 300-400 tokens
- Level 8 (Translation): 200-300 tokens

## Troubleshooting

### API not responding
```bash
# Check if API is running
curl http://localhost:5001/health

# Check port availability
netstat -an | grep 5001
```

### LLM connection issues
- Verify `API_URL` is correct
- Check if LLM server is running
- Test LLM server directly with curl

### CSV processing errors
- Ensure CSV has required columns from previous levels
- Check CSV encoding (should be UTF-8)
- Verify file paths are absolute or relative to API script

## Performance

### Processing Time
- Single item: ~2-5 seconds per level (depends on LLM response time)
- 100 items: ~3-8 minutes per level
- 1000 items: ~30-80 minutes per level

### Optimization Tips
1. Run APIs in parallel for independent items
2. Batch process multiple CSV files
3. Use faster LLM models for production
4. Cache common category mappings

## Dependencies

```python
Flask==2.3.3
pandas==2.0.3
requests==2.31.0
```

Install:
```bash
pip install -r requirements.txt
```

## API Development

To add a new level:

1. Create new API file: `api_X_feature_name.py`
2. Choose a new port: `500X`
3. Define endpoint: `/get_feature_name`
4. Implement feature extraction logic
5. Add to documentation
6. Update pipeline scripts

## Security Notes

- APIs currently run without authentication (add if needed)
- No input validation for file paths (add for production)
- LLM API credentials should be in environment variables
- Use HTTPS in production

## License

See main README.md

## Support

For issues or questions, refer to the main project documentation or create an issue in the repository.
