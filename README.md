# AI Item Data Generator

An AI-powered system for intelligent product categorization, attribute extraction, and multilingual metadata generation for e-commerce platforms.

## Overview

This project provides a comprehensive 8-level processing pipeline that transforms raw product data into richly annotated, searchable, and multilingual e-commerce listings using AI/LLM technology.

## Features

### 8-Level Processing Pipeline

#### Level 1-4: Product Hierarchy / Category Mapping
- **Level 1: shoppingCategory** - Broad category classification (e.g., electronics, fashion, beauty)
- **Level 2: shoppingSubcategory** - Refined category (e.g., headphones, running shoes, skincare)
- **Level 3: itemCategory** - AI-selected precise category within subcategory
- **Level 4: itemSubcategory** - Even more specific classification under itemCategory

#### Level 5: SKW (Search Keywords)
- Generates 5 strict e-commerce search keyword phrases per item
- **Rules:**
  - First keyword = main product category
  - Others = modifier + product (maximum 3 words)
  - Lowercase, no sentiments/numbers/dates
  - Example: `running shoe, lightweight running shoe, nike running shoe`

#### Level 6: DSW (Description Search Words)
- Generates 5-10 descriptive keyword phrases from item name and description
- Focus on tangible features, functional attributes, and proper nouns
- Optimized for search and discovery

#### Level 7: AI Attributes Extraction
- Extracts structured product attributes: Gender, Size, Material, Color, Brand, Product Name, Features, etc.
- Strict format with only inferable attributes
- Leaves unknown attributes empty (no guessing)

#### Level 8: English → Arabic Translation
- Translates key CSV columns: Item (EN), Description (EN), Category/Department (EN) to Arabic
- Professional e-commerce translation
- Arabic only output, no extra text

## Project Structure

```
ai_item_data_generator/
├── flask_apis/              # 8 microservice Flask APIs (one per level)
│   ├── api_1_shopping_category.py
│   ├── api_2_shopping_subcategory.py
│   ├── api_3_item_category.py
│   ├── api_4_item_subcategory.py
│   ├── api_5_skw_generation.py
│   ├── api_6_dsw_generation.py
│   ├── api_7_ai_attributes.py
│   └── api_8_arabic_translation.py
├── mapping.py               # Product category hierarchies and mappings
├── main.ipynb               # Main processing notebook
├── CSVs/                    # Input CSV files
├── output_csvs/             # Processed output files
├── image-feature-extraction/ # Image processing module
└── requirements.txt         # Python dependencies
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai_item_data_generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file with your LLM API configuration:
```
API_URL=http://your-llm-api-url:port/api/generate
MODEL_NAME=phi4:latest
```

## Usage

### Option 1: Using Flask APIs

Each API runs as a microservice on a different port:

```bash
# Start individual APIs
python flask_apis/api_1_shopping_category.py  # Port 5001
python flask_apis/api_2_shopping_subcategory.py  # Port 5002
python flask_apis/api_3_item_category.py  # Port 5003
python flask_apis/api_4_item_subcategory.py  # Port 5004
python flask_apis/api_5_skw_generation.py  # Port 5005
python flask_apis/api_6_dsw_generation.py  # Port 5006
python flask_apis/api_7_ai_attributes.py  # Port 5007
python flask_apis/api_8_arabic_translation.py  # Port 5008
```

### Making API Requests

Example for Level 1 (Shopping Category):
```bash
curl -X POST http://localhost:5001/get_shopping_category \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "input.csv", "output_path": "output.csv"}'
```

### Option 2: Using Jupyter Notebook

Open and run `main.ipynb` for interactive processing.

## Input CSV Format

Expected columns:
- `Item (EN)` - Product name in English
- `Description (EN)` - Product description in English
- `Category/Department (EN)` - Vendor's category classification

## Output

The system enriches your CSV with:
- `shoppingCategory` + `confidence` - Level 1 classification
- `shoppingSubcategory` + `confidence` - Level 2 classification
- `itemCategory` + `confidence` - Level 3 classification
- `itemSubcategory` + `confidence` - Level 4 classification
- `SKW` - Search keywords
- `DSW` - Description search words
- `AI_Attributes` - Structured attributes
- `Item (AR)`, `Description (AR)`, `Category/Department (AR)` - Arabic translations

## Category Hierarchies

The system supports 15 main shopping categories:
- Fashion
- Beauty
- Electronics
- Home and Garden
- Health and Nutrition
- Sports
- Kids
- Pet Care
- Groceries
- Restaurants
- Stationary
- Automotive
- Pharmacies
- Entertainment
- Flowers and Gifts

See `mapping.py` for complete category hierarchies (1000+ categories).

## API Documentation

See [flask_apis/README.md](flask_apis/README.md) for detailed API documentation.

## Technology Stack

- **Python 3.8+**
- **Flask** - Web framework for microservices
- **Pandas** - Data manipulation
- **LLM (Phi-4)** - AI model for classification and extraction
- **OpenAI SDK** - For alternative LLM integration

## Requirements

```
Flask==2.3.3
pandas==2.0.3
requests==2.31.0
numpy==1.24.3
python-dotenv==1.0.0
openai==1.3.0
openpyxl==3.1.2
```

## Development

The project uses a microservices architecture where each processing level is an independent Flask API. This allows for:
- Parallel processing
- Independent scaling
- Modular development
- Easy debugging and testing


