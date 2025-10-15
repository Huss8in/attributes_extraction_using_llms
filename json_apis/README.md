# JSON-Based APIs for Item Data Enrichment

This folder contains JSON-based APIs that accept JSON input and return string outputs for each processing level. Unlike the CSV-based APIs in the `flask_apis` folder, these APIs work with individual item data in JSON format.

## Overview

The system consists of 8 individual processing APIs plus 1 master orchestrator API:

1. **Shopping Category Classification** (Port 6001)
2. **Shopping Subcategory Classification** (Port 6002)
3. **Item Category Classification** (Port 6003)
4. **Item Subcategory Classification** (Port 6004)
5. **SKW (Search Keywords) Generation** (Port 6005)
6. **DSW (Description Search Words) Generation** (Port 6006)
7. **AI Attributes Extraction** (Port 6007)
8. **Arabic Translation** (Port 6008)
9. **Master Pipeline Orchestrator** (Port 6000)

## Quick Start

### 1. Start All APIs

```bash
python json_apis/start_all_json_apis.py
```

This will start all 9 APIs in separate processes.

### 2. Test the APIs

```bash
python json_apis/test_json_master_api.py
```

This will run a complete test of the master pipeline API.

## API Usage

### Master Pipeline API (Recommended)

The master pipeline API orchestrates all 8 levels and returns complete enriched data.

**Endpoint:** `POST http://localhost:6000/process_item`

**Input:**
```json
{
    "item_name": "Cotton T-Shirt",
    "description": "Comfortable casual cotton t-shirt for men",
    "vendor_category": "Clothing"
}
```

**Output:**
```json
{
    "success": true,
    "message": "Item processing completed successfully",
    "total_duration": 45.23,
    "enriched_item": {
        "original_data": {...},
        "shopping_category": "fashion",
        "shopping_category_confidence": 95,
        "shopping_subcategory": "casual wear",
        "shopping_subcategory_confidence": 92,
        "item_category": "t-shirt",
        "item_category_confidence": 98,
        "item_subcategory": "t-shirt",
        "item_subcategory_confidence": 90,
        "skw": "t-shirt, cotton t-shirt, casual t-shirt, ...",
        "dsw": "t-shirt, cotton t-shirt, casual t-shirt, ...",
        "ai_attributes": "Gender: Men\nAge: Adult\n...",
        "item_name_arabic": "قميص قطني"
    },
    "level_results": {...},
    "timestamp": "2025-10-14T..."
}
```

### Individual APIs

You can also call each API individually:

#### 1. Shopping Category Classification

**Endpoint:** `POST http://localhost:6001/classify`

**Input:**
```json
{
    "item_name": "Cotton T-Shirt",
    "description": "Comfortable casual cotton t-shirt",
    "vendor_category": "Clothing"
}
```

**Output:**
```json
{
    "shopping_category": "fashion",
    "confidence": 95
}
```

#### 2. Shopping Subcategory Classification

**Endpoint:** `POST http://localhost:6002/classify`

**Input:**
```json
{
    "shopping_category": "fashion",
    "item_name": "Cotton T-Shirt",
    "description": "Comfortable casual cotton t-shirt",
    "vendor_category": "Clothing"
}
```

**Output:**
```json
{
    "shopping_subcategory": "casual wear",
    "confidence": 92
}
```

#### 3. Item Category Classification

**Endpoint:** `POST http://localhost:6003/classify`

**Input:**
```json
{
    "shopping_category": "fashion",
    "shopping_subcategory": "casual wear",
    "item_name": "Cotton T-Shirt",
    "description": "Comfortable casual cotton t-shirt",
    "vendor_category": "Clothing"
}
```

**Output:**
```json
{
    "item_category": "t-shirt",
    "confidence": 98
}
```

#### 4. Item Subcategory Classification

**Endpoint:** `POST http://localhost:6004/classify`

**Input:**
```json
{
    "shopping_category": "fashion",
    "shopping_subcategory": "casual wear",
    "item_category": "t-shirt",
    "item_name": "Cotton T-Shirt",
    "description": "Comfortable casual cotton t-shirt",
    "vendor_category": "Clothing"
}
```

**Output:**
```json
{
    "item_subcategory": "t-shirt",
    "confidence": 90
}
```

#### 5. SKW Generation

**Endpoint:** `POST http://localhost:6005/generate`

**Input:**
```json
{
    "item_name": "Cotton T-Shirt",
    "description": "Comfortable casual cotton t-shirt",
    "item_category": "t-shirt"
}
```

**Output:**
```json
{
    "skw": "t-shirt, cotton t-shirt, casual t-shirt, comfortable t-shirt, men t-shirt"
}
```

#### 6. DSW Generation

**Endpoint:** `POST http://localhost:6006/generate`

**Input:**
```json
{
    "item_name": "Cotton T-Shirt",
    "description": "Comfortable casual cotton t-shirt",
    "item_category": "t-shirt"
}
```

**Output:**
```json
{
    "dsw": "t-shirt, cotton t-shirt, casual t-shirt, comfortable t-shirt, soft t-shirt"
}
```

#### 7. AI Attributes Extraction

**Endpoint:** `POST http://localhost:6007/extract`

**Input:**
```json
{
    "item_name": "Cotton T-Shirt",
    "description": "Comfortable casual cotton t-shirt for men",
    "vendor_category": "Clothing",
    "shopping_category": "fashion",
    "shopping_subcategory": "casual wear",
    "item_category": "t-shirt"
}
```

**Output:**
```json
{
    "ai_attributes": "Gender: Men\nAge: Adult\nBrand: \nGeneric Name: t-shirt\n..."
}
```

#### 8. Arabic Translation

**Endpoint:** `POST http://localhost:6008/translate`

**Input:**
```json
{
    "text": "Cotton T-Shirt"
}
```

**Output:**
```json
{
    "translation": "قميص قطني"
}
```

## Health Check

All APIs have a health check endpoint:

```bash
curl http://localhost:6001/health
curl http://localhost:6002/health
# ... etc
```

To check all APIs at once:

```bash
curl http://localhost:6000/check_apis
```

## Files

- `json_api_1_shopping_category.py` - Shopping Category Classification API
- `json_api_2_shopping_subcategory.py` - Shopping Subcategory Classification API
- `json_api_3_item_category.py` - Item Category Classification API
- `json_api_4_item_subcategory.py` - Item Subcategory Classification API
- `json_api_5_skw_generation.py` - SKW Generation API
- `json_api_6_dsw_generation.py` - DSW Generation API
- `json_api_7_ai_attributes.py` - AI Attributes Extraction API
- `json_api_8_arabic_translation.py` - Arabic Translation API
- `json_api_master_pipeline.py` - Master Pipeline Orchestrator API
- `start_all_json_apis.py` - Script to start all APIs
- `test_json_master_api.py` - Test script for master API
- `README.md` - This file

## Differences from CSV APIs

| Feature | CSV APIs (flask_apis/) | JSON APIs (json_apis/) |
|---------|----------------------|----------------------|
| Input | CSV file path | JSON object |
| Output | CSV file + metadata | JSON string/object |
| Batch Processing | Yes (entire CSV) | No (single item) |
| Use Case | Processing CSV files | Real-time item enrichment |
| Port Range | 5001-5008 | 6001-6008 |

## Requirements

- Python 3.7+
- Flask
- requests
- Access to AI model at `http://100.75.237.4:11434`

## Troubleshooting

**APIs not starting:**
- Check if ports 6000-6008 are available
- Ensure Python dependencies are installed: `pip install flask requests`

**AI model errors:**
- Verify the AI model endpoint is accessible: `http://100.75.237.4:11434`
- Check if the required models (phi4:latest, aya:8b) are loaded

**Timeout errors:**
- Increase timeout values in the API calls
- Check network connectivity to the AI model server

## Notes

- All APIs use the same AI models as the CSV-based APIs
- The master pipeline processes items sequentially through all 8 levels
- Each level depends on the output of previous levels
- Processing time depends on AI model response time (typically 5-10s per level)
