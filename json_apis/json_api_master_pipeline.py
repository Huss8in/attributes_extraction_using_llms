"""
JSON Master Pipeline API
Orchestrates all 8 processing levels for a single item
Accepts JSON input and returns complete enriched data
"""

import sys
import io

# Set UTF-8 encoding for stdout to handle Arabic text
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, request, jsonify
import requests
import time
from datetime import datetime

app = Flask(__name__)

# API endpoints for each level
API_ENDPOINTS = {
    "level_1": "http://localhost:6001/classify",
    "level_2": "http://localhost:6002/classify",
    "level_3": "http://localhost:6003/classify",
    "level_4": "http://localhost:6004/classify",
    "level_5": "http://localhost:6005/generate",
    "level_6": "http://localhost:6006/generate",
    "level_7": "http://localhost:6007/extract",
    "level_8": "http://localhost:6008/translate"
}

LEVEL_NAMES = {
    "level_1": "Shopping Category",
    "level_2": "Shopping Subcategory",
    "level_3": "Item Category",
    "level_4": "Item Subcategory",
    "level_5": "SKW Generation",
    "level_6": "DSW Generation",
    "level_7": "AI Attributes",
    "level_8": "Arabic Translation"
}


def check_api_health(endpoint):
    """Check if an API endpoint is healthy"""
    try:
        # Get base URL and add /health
        base_url = endpoint.rsplit('/', 1)[0]
        health_url = f"{base_url}/health"
        response = requests.get(health_url, timeout=5)
        return response.status_code == 200
    except:
        return False


def call_level_1(item_data):
    """Level 1: Shopping Category Classification"""
    payload = {
        "item_name": item_data.get("item_name", ""),
        "description": item_data.get("description", ""),
        "vendor_category": item_data.get("vendor_category", "")
    }
    response = requests.post(API_ENDPOINTS["level_1"], json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_level_2(item_data, level_1_result):
    """Level 2: Shopping Subcategory Classification"""
    payload = {
        "shopping_category": level_1_result.get("shopping_category", ""),
        "item_name": item_data.get("item_name", ""),
        "description": item_data.get("description", ""),
        "vendor_category": item_data.get("vendor_category", "")
    }
    response = requests.post(API_ENDPOINTS["level_2"], json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_level_3(item_data, level_1_result, level_2_result):
    """Level 3: Item Category Classification"""
    payload = {
        "shopping_category": level_1_result.get("shopping_category", ""),
        "shopping_subcategory": level_2_result.get("shopping_subcategory", ""),
        "item_name": item_data.get("item_name", ""),
        "description": item_data.get("description", ""),
        "vendor_category": item_data.get("vendor_category", "")
    }
    response = requests.post(API_ENDPOINTS["level_3"], json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_level_4(item_data, level_1_result, level_2_result, level_3_result):
    """Level 4: Item Subcategory Classification"""
    payload = {
        "shopping_category": level_1_result.get("shopping_category", ""),
        "shopping_subcategory": level_2_result.get("shopping_subcategory", ""),
        "item_category": level_3_result.get("item_category", ""),
        "item_name": item_data.get("item_name", ""),
        "description": item_data.get("description", ""),
        "vendor_category": item_data.get("vendor_category", "")
    }
    response = requests.post(API_ENDPOINTS["level_4"], json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_level_5(item_data, level_3_result):
    """Level 5: SKW Generation"""
    payload = {
        "item_name": item_data.get("item_name", ""),
        "description": item_data.get("description", ""),
        "item_category": level_3_result.get("item_category", "")
    }
    response = requests.post(API_ENDPOINTS["level_5"], json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_level_6(item_data, level_3_result):
    """Level 6: DSW Generation"""
    payload = {
        "item_name": item_data.get("item_name", ""),
        "description": item_data.get("description", ""),
        "item_category": level_3_result.get("item_category", "")
    }
    response = requests.post(API_ENDPOINTS["level_6"], json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_level_7(item_data, level_1_result, level_2_result, level_3_result):
    """Level 7: AI Attributes Extraction"""
    payload = {
        "item_name": item_data.get("item_name", ""),
        "description": item_data.get("description", ""),
        "vendor_category": item_data.get("vendor_category", ""),
        "shopping_category": level_1_result.get("shopping_category", ""),
        "shopping_subcategory": level_2_result.get("shopping_subcategory", ""),
        "item_category": level_3_result.get("item_category", "")
    }
    response = requests.post(API_ENDPOINTS["level_7"], json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_level_8(text):
    """Level 8: Arabic Translation"""
    payload = {"text": text}
    response = requests.post(API_ENDPOINTS["level_8"], json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


@app.route('/process_item', methods=['POST'])
def process_item():
    """
    Process a single item through all 8 levels

    Input JSON:
    {
        "item_name": "Cotton T-Shirt",
        "description": "Comfortable casual cotton t-shirt",
        "vendor_category": "Clothing"
    }

    Returns complete enriched item data with all classifications and attributes
    """
    start_time = time.time()

    try:
        item_data = request.get_json()

        item_name = item_data.get('item_name', '')
        if not item_name:
            return jsonify({"error": "item_name is required"}), 400

        print(f"\n{'='*60}")
        print(f"Processing Item: {item_name}")
        print(f"{'='*60}\n")

        results = {}

        # Level 1: Shopping Category
        print("[Level 1/8] Shopping Category...")
        level_start = time.time()
        level_1_result = call_level_1(item_data)
        results["level_1"] = {
            "name": LEVEL_NAMES["level_1"],
            "duration": round(time.time() - level_start, 2),
            "data": level_1_result
        }
        print(f"  OK {level_1_result.get('shopping_category', 'N/A')} ({level_1_result.get('confidence', 0)}%)")

        # Level 2: Shopping Subcategory
        print("[Level 2/8] Shopping Subcategory...")
        level_start = time.time()
        level_2_result = call_level_2(item_data, level_1_result)
        results["level_2"] = {
            "name": LEVEL_NAMES["level_2"],
            "duration": round(time.time() - level_start, 2),
            "data": level_2_result
        }
        print(f"  OK {level_2_result.get('shopping_subcategory', 'N/A')} ({level_2_result.get('confidence', 0)}%)")

        # Level 3: Item Category
        print("[Level 3/8] Item Category...")
        level_start = time.time()
        level_3_result = call_level_3(item_data, level_1_result, level_2_result)
        results["level_3"] = {
            "name": LEVEL_NAMES["level_3"],
            "duration": round(time.time() - level_start, 2),
            "data": level_3_result
        }
        print(f"  OK {level_3_result.get('item_category', 'N/A')} ({level_3_result.get('confidence', 0)}%)")

        # Level 4: Item Subcategory
        print("[Level 4/8] Item Subcategory...")
        level_start = time.time()
        level_4_result = call_level_4(item_data, level_1_result, level_2_result, level_3_result)
        results["level_4"] = {
            "name": LEVEL_NAMES["level_4"],
            "duration": round(time.time() - level_start, 2),
            "data": level_4_result
        }
        print(f"  OK {level_4_result.get('item_subcategory', 'N/A')} ({level_4_result.get('confidence', 0)}%)")

        # Level 5: SKW Generation
        print("[Level 5/8] SKW Generation...")
        level_start = time.time()
        level_5_result = call_level_5(item_data, level_3_result)
        results["level_5"] = {
            "name": LEVEL_NAMES["level_5"],
            "duration": round(time.time() - level_start, 2),
            "data": level_5_result
        }
        print(f"  OK {level_5_result.get('skw', 'N/A')[:50]}...")

        # Level 6: DSW Generation
        print("[Level 6/8] DSW Generation...")
        level_start = time.time()
        level_6_result = call_level_6(item_data, level_3_result)
        results["level_6"] = {
            "name": LEVEL_NAMES["level_6"],
            "duration": round(time.time() - level_start, 2),
            "data": level_6_result
        }
        print(f"  OK {level_6_result.get('dsw', 'N/A')[:50]}...")

        # Level 7: AI Attributes
        print("[Level 7/8] AI Attributes...")
        level_start = time.time()
        level_7_result = call_level_7(item_data, level_1_result, level_2_result, level_3_result)
        results["level_7"] = {
            "name": LEVEL_NAMES["level_7"],
            "duration": round(time.time() - level_start, 2),
            "data": level_7_result
        }
        print(f"  OK Attributes extracted")

        # Level 8: Arabic Translation (translate item name)
        print("[Level 8/8] Arabic Translation...")
        level_start = time.time()
        level_8_result = call_level_8(item_name)
        results["level_8"] = {
            "name": LEVEL_NAMES["level_8"],
            "duration": round(time.time() - level_start, 2),
            "data": level_8_result
        }
        # Avoid printing Arabic text due to Windows console encoding issues
        translation = level_8_result.get('translation', 'N/A')
        try:
            print(f"  OK {translation}")
        except UnicodeEncodeError:
            print(f"  OK [Arabic text - {len(translation)} chars]")

        total_duration = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"Processing Complete!")
        print(f"Total time: {round(total_duration, 2)}s")
        print(f"{'='*60}\n")

        # Build enriched item data
        enriched_item = {
            "original_data": item_data,
            "shopping_category": level_1_result.get("shopping_category", ""),
            "shopping_category_confidence": level_1_result.get("confidence", 0),
            "shopping_subcategory": level_2_result.get("shopping_subcategory", ""),
            "shopping_subcategory_confidence": level_2_result.get("confidence", 0),
            "item_category": level_3_result.get("item_category", ""),
            "item_category_confidence": level_3_result.get("confidence", 0),
            "item_subcategory": level_4_result.get("item_subcategory", ""),
            "item_subcategory_confidence": level_4_result.get("confidence", 0),
            "skw": level_5_result.get("skw", ""),
            "dsw": level_6_result.get("dsw", ""),
            "ai_attributes": level_7_result.get("ai_attributes", ""),
            "item_name_arabic": level_8_result.get("translation", "")
        }

        return jsonify({
            "success": True,
            "message": "Item processing completed successfully",
            "total_duration": round(total_duration, 2),
            "enriched_item": enriched_item,
            "level_results": results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Item processing failed"
        }), 500


@app.route('/check_apis', methods=['GET'])
def check_apis():
    """Check health status of all API endpoints"""
    status = {}
    all_healthy = True

    for level_key, endpoint in API_ENDPOINTS.items():
        level_name = LEVEL_NAMES[level_key]
        is_healthy = check_api_health(endpoint)
        status[level_key] = {
            "name": level_name,
            "endpoint": endpoint,
            "status": "healthy" if is_healthy else "unavailable"
        }
        if not is_healthy:
            all_healthy = False

    return jsonify({
        "all_healthy": all_healthy,
        "apis": status,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON Master Pipeline API",
        "levels": 8
    })


@app.route('/', methods=['GET'])
def index():
    """API information endpoint"""
    return jsonify({
        "service": "JSON Master Pipeline API",
        "version": "1.0.0",
        "description": "Full 8-level product data enrichment pipeline for JSON input",
        "endpoints": {
            "/process_item": "Process single item through pipeline (POST)",
            "/check_apis": "Check health of all API endpoints (GET)",
            "/health": "Health check (GET)"
        },
        "levels": LEVEL_NAMES,
        "api_endpoints": API_ENDPOINTS
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON Master Pipeline API - Full 8-Level Processing")
    print("="*60)
    print("\nThis API orchestrates all 8 processing levels:")
    for level_num in range(1, 9):
        level_key = f"level_{level_num}"
        print(f"  {level_num}. {LEVEL_NAMES[level_key]}")
    print("\n" + "="*60)
    print("\nAPI Endpoints:")
    print("  POST /process_item  - Process single item")
    print("  GET  /check_apis    - Check all API health")
    print("  GET  /health        - Health check")
    print("\n" + "="*60)
    print("\nStarting JSON Master Pipeline API on http://localhost:6000")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6000)
