"""
Image Feature Extraction Script
Extracts features from one or multiple images using BLIP-MAE model
Supports majority voting when multiple images are provided
"""

import torch
import transformers
import os
import json
from dotenv import load_dotenv
from collections import Counter
from typing import List, Dict, Any

load_dotenv()

device = "cuda" if torch.cuda.is_available() else "cpu"
secret_value = os.getenv("HF_TOKEN")  # Hugging Face access token

# --------------------------------------------------------------------------------------------------------------------
# Monkey-patch to fix the GenerationMixin issue with custom models
original_add_generation_mixin = (
    transformers.models.auto.auto_factory.add_generation_mixin_to_remote_model
)


def patched_add_generation_mixin(model_class):
    try:
        return original_add_generation_mixin(model_class)
    except AttributeError:
        # If the model doesn't have prepare_inputs_for_generation, skip adding GenerationMixin
        return model_class


transformers.models.auto.auto_factory.add_generation_mixin_to_remote_model = (
    patched_add_generation_mixin
)
# --------------------------------------------------------------------------------------------------------------------

# Load the model
from transformers import AutoModel

print(f"Using device: {device}")
print("Loading BLIP-MAE model...")

model = AutoModel.from_pretrained(
    "Blip-MAE-Botit/BlipMAEModel",
    trust_remote_code=True,
    token=secret_value,
    use_pretrained_botit_data=False,  # Use default weights instead of custom Botit weights
    device=device,
    repo_id="Salesforce/blip-vqa-base",  # Use BLIP base model tokenizer
)

print("Model loaded successfully!\n")


def extract_features(
    image_urls: List[str],
    description: str,
    category: str,
    attributes: List[str] = ["color", "material"],
    use_majority_voting: bool = True
) -> Dict[str, Any]:
    """
    Extract features from one or multiple images

    Args:
        image_urls: List of image URLs (can be single or multiple)
        description: Item description text
        category: Item category (e.g., 'bags', 'clothing', 'shoes')
        attributes: List of attributes to extract (default: ['color', 'material'])
        use_majority_voting: If True and multiple images provided, use majority voting

    Returns:
        Dictionary with extracted features and confidences
    """
    # Prepare input for model
    descriptions = [description] * len(image_urls)
    categories = [category] * len(image_urls)

    print(f"Processing {len(image_urls)} image(s)...")
    print(f"Description: {description}")
    print(f"Category: {category}")
    print(f"Attributes: {attributes}\n")

    # Extract features using the model
    results = model.generate(
        images_pth=image_urls,
        descriptions=descriptions,
        categories=categories,
        attributes=attributes,
        return_confidences=True,
    )

    if len(image_urls) == 1 or not use_majority_voting:
        # Single image or no majority voting - return as is
        return {
            "method": "single_image" if len(image_urls) == 1 else "no_voting",
            "num_images": len(image_urls),
            "results": results,
            "final_features": results[0] if results else {}
        }

    # Multiple images - apply majority voting
    print(f"Applying majority voting across {len(image_urls)} images...")

    final_features = {}
    voting_details = {}

    for attr in attributes:
        values = []
        confidences = []

        # Collect all values and confidences for this attribute
        for img_result in results:
            if img_result and attr in img_result[0]:
                attr_data = img_result[0][attr]
                values.append(attr_data['value'])
                confidences.append(attr_data['confidence'])

        if values:
            # Count occurrences of each value
            value_counts = Counter(values)
            most_common_value, count = value_counts.most_common(1)[0]

            # Calculate average confidence for the most common value
            avg_confidence = sum(
                conf for val, conf in zip(values, confidences)
                if val == most_common_value
            ) / count

            final_features[attr] = {
                'value': most_common_value,
                'confidence': avg_confidence,
                'votes': count,
                'total_images': len(values)
            }

            voting_details[attr] = {
                'all_values': values,
                'all_confidences': confidences,
                'value_counts': dict(value_counts),
                'selected_value': most_common_value,
                'vote_percentage': (count / len(values)) * 100
            }

    return {
        "method": "majority_voting",
        "num_images": len(image_urls),
        "results": results,
        "final_features": final_features,
        "voting_details": voting_details
    }


def process_item(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single item with image feature extraction

    Args:
        input_data: Dictionary with keys:
            - image_urls: List of image URLs (required)
            - description: Item description (required)
            - category: Item category (required)
            - attributes: List of attributes to extract (optional, default: ['color', 'material'])
            - use_majority_voting: Boolean (optional, default: True)

    Returns:
        Dictionary with extraction results
    """
    image_urls = input_data.get('image_urls', [])
    description = input_data.get('description', '')
    category = input_data.get('category', '')
    attributes = input_data.get('attributes', ['color', 'material'])
    use_majority_voting = input_data.get('use_majority_voting', True)

    if not image_urls:
        return {"error": "No image URLs provided"}

    if not description:
        return {"error": "No description provided"}

    if not category:
        return {"error": "No category provided"}

    return extract_features(
        image_urls=image_urls,
        description=description,
        category=category,
        attributes=attributes,
        use_majority_voting=use_majority_voting
    )


# --------------------------------------------------------------------------------------------------------------------
# Example usage
# --------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Example 1: Single image
    print("="*80)
    print("Example 1: Single Image")
    print("="*80)

    single_image_input = {
        "image_urls": ["https://dfcdn.defacto.com.tr/6/B9037AX_NS_NV144_01_03.jpg"],
        "description": "Woman Straw Shopping Bag",
        "category": "bags",
        "attributes": ["color", "material"]
    }

    result1 = process_item(single_image_input)
    print("\nFinal Features:")
    print(json.dumps(result1['final_features'], indent=2))
    print("\n")

    # Example 2: Multiple images with majority voting
    print("="*80)
    print("Example 2: Multiple Images with Majority Voting")
    print("="*80)

    multiple_images_input = {
        "image_urls": [
            "https://dfcdn.defacto.com.tr/6/B9037AX_NS_NV144_01_03.jpg",
            "https://dfcdn.defacto.com.tr/6/B9037AX_NS_NV144_01_01.jpg",
            "https://dfcdn.defacto.com.tr/6/B9037AX_NS_NV144_01_02.jpg"
        ],
        "description": "Woman Straw Shopping Bag",
        "category": "bags",
        "attributes": ["color", "material"],
        "use_majority_voting": True
    }

    result2 = process_item(multiple_images_input)
    print("\nFinal Features (after majority voting):")
    print(json.dumps(result2['final_features'], indent=2))

    if 'voting_details' in result2:
        print("\nVoting Details:")
        for attr, details in result2['voting_details'].items():
            print(f"\n{attr.upper()}:")
            print(f"  Selected: {details['selected_value']}")
            print(f"  Vote %: {details['vote_percentage']:.1f}%")
            print(f"  All values: {details['all_values']}")
            print(f"  Value counts: {details['value_counts']}")

    print("\n" + "="*80)
    print("Complete!")
    print("="*80)
