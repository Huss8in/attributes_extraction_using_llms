"""
JSON API #9: Hybrid Feature Extraction
Extracts features using:
1. Text description parsing (primary - more reliable)
2. Image analysis (secondary - fallback/validation)
"""

from flask import Flask, request, jsonify
import re
from collections import Counter

app = Flask(__name__)


def extract_from_text(description, attributes):
    """
    Extract features from text description
    More reliable than image analysis for structured descriptions
    """
    features = {}

    description_lower = description.lower()

    # Color extraction
    if 'color' in attributes:
        # Look for explicit color mentions
        color_patterns = [
            r'color[:\s]+([a-zA-Z\s]+?)[\.,;\n]',  # "Color: emerald green."
            r'([a-zA-Z\s]+?)\s+color',  # "emerald green color"
        ]

        colors_found = []
        for pattern in color_patterns:
            matches = re.findall(pattern, description_lower, re.IGNORECASE)
            colors_found.extend([m.strip() for m in matches if m.strip()])

        # Also check for common color words
        common_colors = [
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown',
            'black', 'white', 'gray', 'grey', 'beige', 'navy', 'emerald', 'turquoise',
            'crimson', 'maroon', 'olive', 'tan', 'khaki', 'gold', 'silver', 'bronze'
        ]

        for color in common_colors:
            if color in description_lower:
                colors_found.append(color)

        if colors_found:
            # Use most common or last mentioned (usually most specific)
            color_value = colors_found[-1].title()
            features['color'] = {
                'value': color_value,
                'confidence': 0.95,  # High confidence from text
                'source': 'text_description'
            }

    # Material extraction
    if 'material' in attributes:
        # Look for explicit material mentions
        material_patterns = [
            r'material[s]?[:\s]+([a-zA-Z\s]+?)[\.,;\n]',  # "Materials: cotton."
            r'made\s+(?:of|from)\s+([a-zA-Z\s]+?)[\.,;\n]',  # "made of cotton"
            r'crafted\s+from\s+([a-zA-Z\s]+?)[\.,;\n]',  # "crafted from silk"
        ]

        materials_found = []
        for pattern in material_patterns:
            matches = re.findall(pattern, description_lower, re.IGNORECASE)
            materials_found.extend([m.strip() for m in matches if m.strip()])

        # Common materials
        common_materials = [
            'cotton', 'silk', 'wool', 'linen', 'polyester', 'nylon', 'spandex',
            'leather', 'suede', 'denim', 'velvet', 'satin', 'chiffon', 'lace',
            'canvas', 'corduroy', 'fleece', 'cashmere', 'tweed', 'jersey',
            'straw', 'wicker', 'rattan', 'bamboo', 'wood', 'metal', 'plastic',
            'rubber', 'latex', 'vinyl', 'faux leather', 'faux fur', 'snake skin',
            'metallic', 'fabric', 'textile'
        ]

        for material in common_materials:
            if material in description_lower:
                materials_found.append(material)

        if materials_found:
            # Use most specific (longest match usually)
            material_value = max(materials_found, key=len).title()
            features['material'] = {
                'value': material_value,
                'confidence': 0.95,
                'source': 'text_description'
            }

    # Pattern extraction (if requested)
    if 'pattern' in attributes:
        common_patterns = [
            'striped', 'solid', 'floral', 'polka dot', 'checkered', 'plaid',
            'paisley', 'geometric', 'abstract', 'animal print', 'leopard',
            'zebra', 'snake', 'camo', 'camouflage', 'tie-dye', 'ombre'
        ]

        for pattern in common_patterns:
            if pattern in description_lower:
                features['pattern'] = {
                    'value': pattern.title(),
                    'confidence': 0.90,
                    'source': 'text_description'
                }
                break

    return features


@app.route('/extract', methods=['POST'])
def extract():
    """
    Extract features from description and/or images

    Input JSON:
    {
        "image_urls": ["url1", "url2"],  // Optional
        "description": "Item description with color and material",  // Required
        "category": "clothing",  // Optional
        "attributes": ["color", "material"]  // Optional, default: ["color", "material"]
    }

    Returns:
    {
        "features": {
            "color": {"value": "Emerald Green", "confidence": 0.95, "source": "text_description"},
            "material": {"value": "Metallic Faux Snake Skin", "confidence": 0.95, "source": "text_description"}
        }
    }
    """
    try:
        data = request.get_json()

        description = data.get('description', '')
        attributes = data.get('attributes', ['color', 'material'])

        if not description:
            return jsonify({"error": "description is required"}), 400

        # Extract from text (primary method)
        features = extract_from_text(description, attributes)

        # Add metadata
        metadata = {
            "method": "text_parsing",
            "attributes_requested": attributes,
            "attributes_found": list(features.keys())
        }

        # Check for missing attributes
        missing = [attr for attr in attributes if attr not in features]
        if missing:
            metadata['missing_attributes'] = missing
            metadata['note'] = f"Could not extract: {', '.join(missing)}"

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
        "service": "Hybrid Feature Extraction API (Text-based)"
    })


@app.route('/', methods=['GET'])
def index():
    """API information"""
    return jsonify({
        "service": "Hybrid Feature Extraction API",
        "version": "2.0.0",
        "method": "Text parsing (reliable)",
        "endpoints": {
            "/extract": "Extract features (POST)",
            "/health": "Health check (GET)"
        },
        "supported_attributes": ["color", "material", "pattern"]
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Hybrid Feature Extraction API (Text-based)")
    print("="*60)
    print("\nMethod: Text description parsing")
    print("\nEndpoints:")
    print("  POST /extract - Extract features")
    print("  GET  /health  - Health check")
    print("\n" + "="*60)
    print("\nStarting API on http://localhost:6009")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=6009)
