"""
JSON API #9: Image Feature Extraction
Accepts JSON input with image URLs and returns extracted features (color, material, etc.)
Supports multiple images with majority voting
"""

from flask import Flask, request, jsonify
import torch
import transformers
import os
import requests
import tempfile
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

app = Flask(__name__)

device = "cuda" if torch.cuda.is_available() else "cpu"
secret_value = os.getenv("HF_TOKEN")

# Monkey-patch fix
original_add_generation_mixin = (
    transformers.models.auto.auto_factory.add_generation_mixin_to_remote_model
)


def patched_add_generation_mixin(model_class):
    try:
        return original_add_generation_mixin(model_class)
    except AttributeError:
        return model_class


transformers.models.auto.auto_factory.add_generation_mixin_to_remote_model = (
    patched_add_generation_mixin
)

# Load model
from transformers import AutoModel

print(f"Loading BLIP-MAE model on {device}...")
model = AutoModel.from_pretrained(
    "Blip-MAE-Botit/BlipMAEModel",
    trust_remote_code=True,
    token=secret_value,
    use_pretrained_botit_data=False,
    device=device,
    repo_id="Salesforce/blip-vqa-base",
)
print("Model loaded successfully!")


def preprocess_images(image_urls):
    """
    Pre-download and validate images before sending to model
    This helps with Azure Blob Storage and other protected URLs
    """
    processed_urls = []

    for i, url in enumerate(image_urls):
        try:
            print(f"[INFO] Pre-processing image {i+1}/{len(image_urls)}: {url[:80]}...")

            # Download image
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                print(f"[WARNING] Failed to download image {i+1}: HTTP {response.status_code}")
                continue

            # Validate it's an image
            img = Image.open(BytesIO(response.content))
            print(f"[INFO] Image {i+1}: {img.format} {img.size} {img.mode}")

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
                print(f"[INFO] Converted image {i+1} to RGB")

            # Save to temp file (helps with model compatibility)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                img.save(tmp.name, 'JPEG')
                processed_urls.append(tmp.name)
                print(f"[INFO] Saved image {i+1} to temp file: {tmp.name}")

        except Exception as e:
            print(f"[ERROR] Failed to process image {i+1}: {e}")
            continue

    return processed_urls


def extract_features_with_voting(image_urls, description, category, attributes):
    """Extract features from images with majority voting"""
    print(f"[DEBUG] Processing {len(image_urls)} images")
    print(f"[DEBUG] Description: {description}")
    print(f"[DEBUG] Category: {category}")
    print(f"[DEBUG] Attributes: {attributes}")

    # Pre-process images (download and validate)
    processed_images = preprocess_images(image_urls)

    if not processed_images:
        print(f"[ERROR] No valid images could be processed")
        return {}, {
            "method": "error",
            "num_images": 0,
            "error": "Failed to download/process any images"
        }

    print(f"[INFO] Successfully processed {len(processed_images)}/{len(image_urls)} images")

    # Prepare inputs
    descriptions = [description] * len(processed_images)
    categories = [category] * len(processed_images)

    # Get model predictions
    try:
        # First attempt with original description
        results = model.generate(
            images_pth=processed_images,
            descriptions=descriptions,
            categories=categories,
            attributes=attributes,
            return_confidences=True,
        )
        print(f"[DEBUG] Attempt 1 - Raw results: {results}")

        # Check if we got valid results
        has_valid_results = False
        if results:
            for img_result in results:
                if img_result and img_result[0]:
                    for attr, data in img_result[0].items():
                        if data['value'].lower() not in ['no', 'n/a', 'none', 'unknown']:
                            has_valid_results = True
                            break
                if has_valid_results:
                    break

        # If no valid results, try with simplified description
        if not has_valid_results:
            print("[INFO] No valid results with original description, trying simplified version...")

            # Extract key words from description
            import re
            words = re.findall(r'\b\w+\b', description.lower())
            material_keywords = ['cotton', 'silk', 'wool', 'leather', 'denim', 'polyester',
                               'linen', 'satin', 'velvet', 'suede', 'fabric', 'textile',
                               'snake skin', 'metallic', 'faux', 'straw']
            color_keywords = ['red', 'blue', 'green', 'black', 'white', 'brown', 'gray',
                            'yellow', 'pink', 'purple', 'orange', 'beige', 'navy', 'emerald']

            found_materials = [w for w in material_keywords if w in description.lower()]
            found_colors = [w for w in color_keywords if w in description.lower()]

            # Create a simpler description
            simple_desc = category.replace('_', ' ')
            if found_materials:
                simple_desc += ' made of ' + ', '.join(found_materials)
            if found_colors:
                simple_desc += ' in ' + ', '.join(found_colors) + ' color'

            print(f"[INFO] Trying with simplified description: '{simple_desc}'")

            simple_descriptions = [simple_desc] * len(processed_images)

            results = model.generate(
                images_pth=processed_images,
                descriptions=simple_descriptions,
                categories=categories,
                attributes=attributes,
                return_confidences=True,
            )
            print(f"[DEBUG] Attempt 2 - Simplified results: {results}")

    finally:
        # Clean up temp files
        import os
        for tmp_file in processed_images:
            try:
                os.unlink(tmp_file)
            except:
                pass

    # Single image - return directly (but filter out "no" values)
    if len(image_urls) == 1:
        if results and results[0] and results[0][0]:
            cleaned_features = {}
            for attr, data in results[0][0].items():
                if data['value'].lower() not in ['no', 'n/a', 'none', 'unknown']:
                    cleaned_features[attr] = data
                else:
                    print(f"[WARNING] Got invalid value '{data['value']}' for {attr}")
            return cleaned_features, {"method": "single_image", "warning": "Some features returned 'no'"}

    # Multiple images - majority voting
    final_features = {}
    voting_details = {}

    for attr in attributes:
        values = []
        confidences = []

        # Collect values from all images, filtering out "no" responses
        for img_result in results:
            if img_result and img_result[0] and attr in img_result[0]:
                attr_data = img_result[0][attr]
                value = attr_data['value'].lower()

                # Skip invalid values
                if value not in ['no', 'n/a', 'none', 'unknown']:
                    values.append(attr_data['value'])
                    confidences.append(attr_data['confidence'])
                else:
                    print(f"[WARNING] Skipping invalid value '{attr_data['value']}' for {attr}")

        if values:
            # Find most common value
            value_counts = Counter(values)
            most_common_value, count = value_counts.most_common(1)[0]

            # Average confidence for most common value
            avg_confidence = sum(
                conf for val, conf in zip(values, confidences)
                if val == most_common_value
            ) / count

            final_features[attr] = {
                'value': most_common_value,
                'confidence': avg_confidence
            }

            voting_details[attr] = {
                'votes': count,
                'total_images': len(values),
                'vote_percentage': (count / len(values)) * 100,
                'all_values': values
            }
        else:
            print(f"[ERROR] No valid values found for {attr}")

    return final_features, {
        "method": "majority_voting",
        "num_images": len(image_urls),
        "voting_details": voting_details
    }


@app.route('/extract', methods=['POST'])
def extract():
    """
    Extract image features

    Input JSON:
    {
        "image_urls": ["url1", "url2", ...],
        "description": "Item description",
        "category": "bags",
        "attributes": ["color", "material"]
    }

    Returns:
    {
        "features": {
            "color": {"value": "Green", "confidence": 0.95},
            "material": {"value": "Straw", "confidence": 0.88}
        },
        "metadata": {...}
    }
    """
    try:
        data = request.get_json()

        image_urls = data.get('image_urls', [])
        description = data.get('description', '')
        category = data.get('category', '')
        attributes = data.get('attributes', ['color', 'material'])

        if not image_urls:
            return jsonify({"error": "image_urls is required"}), 400

        if not description:
            return jsonify({"error": "description is required"}), 400

        if not category:
            return jsonify({"error": "category is required"}), 400

        # Category mapping - map common categories to model-recognized ones
        category_mapping = {
            'trousers': 'clothing',
            'pants': 'clothing',
            'jeans': 'clothing',
            'dress': 'clothing',
            'shirt': 'clothing',
            'blouse': 'clothing',
            'skirt': 'clothing',
            't-shirt': 'clothing',
            'jacket': 'clothing',
            'coat': 'clothing',
            'sweater': 'clothing',
            'shorts': 'clothing',
            'handbag': 'bags',
            'purse': 'bags',
            'backpack': 'bags',
            'wallet': 'bags',
            'sneakers': 'shoes',
            'boots': 'shoes',
            'sandals': 'shoes',
            'heels': 'shoes',
            'flats': 'shoes',
            'watch': 'accessories',
            'belt': 'accessories',
            'scarf': 'accessories',
            'hat': 'accessories',
            'sunglasses': 'accessories',
            'necklace': 'jewelry',
            'ring': 'jewelry',
            'bracelet': 'jewelry',
            'earrings': 'jewelry'
        }

        # Map category to model-recognized category
        original_category = category
        category = category_mapping.get(category.lower(), category)

        if original_category != category:
            print(f"[INFO] Mapped category '{original_category}' -> '{category}'")

        # Extract features
        features, metadata = extract_features_with_voting(
            image_urls, description, category, attributes
        )

        # Add original category to metadata
        metadata['original_category'] = original_category
        metadata['mapped_category'] = category

        return jsonify({
            "features": features,
            "metadata": metadata
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "JSON Image Feature Extraction API",
        "device": device
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "JSON Image Feature Extraction API",
        "version": "1.0.0",
        "model": "BLIP-MAE",
        "device": device,
        "endpoints": {
            "/extract": "Extract image features (POST)",
            "/health": "Health check (GET)"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JSON Image Feature Extraction API")
    print("="*60)
    print(f"\nDevice: {device}")
    print("\nEndpoints:")
    print("  POST /extract - Extract image features")
    print("  GET  /health  - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6009")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6009)
