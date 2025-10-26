import torch
import transformers
import os
import pandas as pd
from dotenv import load_dotenv
import json
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

device = "cuda" if torch.cuda.is_available() else "cpu"
secret_value = os.getenv("HF_TOKEN")

# -------------------------------------------------------------------------------------------------------------------- #

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

# -------------------------------------------------------------------------------------------------------------------- #

print(f"Using device: {device}")
print("Loading model...")

from transformers import AutoModel

model = AutoModel.from_pretrained(
    "Blip-MAE-Botit/BlipMAEModel",
    trust_remote_code=True,
    token=secret_value,
    use_pretrained_botit_data=False,
    device=device,
    repo_id="Salesforce/blip-vqa-base",
)

print("Model loaded successfully!\n")

# -------------------------------------------------------------------------------------------------------------------- #

# Read CSV (skip first row which is general info, use row 2 as header, skip row 3 which is Arabic headers)
print("Reading CSV file...")
df = pd.read_csv('Hy-by-Haya-fashion.csv', skiprows=[0, 2], encoding='utf-8')

# Remove rows where 'Item (EN)' is NaN or empty (these are not valid products)
df = df[df['Item (EN)'].notna() & (df['Item (EN)'] != '')]
df = df.reset_index(drop=True)

print(f"Found {len(df)} valid products\n")

# Define attributes to extract
attributes_to_extract = ["color", "material", "style", "pattern"]

# TEST MODE: Process only first N products (change to None to process all)
TEST_LIMIT = None
if TEST_LIMIT:
    df = df.head(TEST_LIMIT)
    print(f"TEST MODE: Processing only first {TEST_LIMIT} products\n")
else:
    print(f"Processing all {len(df)} products\n")

# Process each product
results_list = []
output_file = 'Haya_extracted_features.csv'

for idx, row in df.iterrows():
    print(f"Processing product {idx + 1}/{len(df)}: {row['Item (EN)']}")

    # Get images (split by comma)
    image_links = row['Image link (comma seperated)']
    if pd.isna(image_links):
        print("  No images found, skipping...")
        continue

    # Split images and clean
    images = [img.strip() for img in str(image_links).split(',') if img.strip()]
    if not images:
        print("  No valid images found, skipping...")
        continue

    # Use first image for feature extraction
    first_image = images[0]

    # Get description and category
    description = str(row['Description (EN)']) if pd.notna(row['Description (EN)']) else ""
    category = str(row['Category/Department (EN)']) if pd.notna(row['Category/Department (EN)']) else "clothing"

    # Clean description (remove extra whitespace, newlines)
    description = " ".join(description.split())

    try:
        # Extract features using the model
        results = model.generate(
            images_pth=[first_image],
            descriptions=[description],
            categories=[category],
            attributes=attributes_to_extract,
            return_confidences=True
        )

        # Parse results
        extracted_attributes = results[0][0] if results else {}

        # Convert numpy types to Python types for JSON serialization
        extracted_attributes_json = {}
        for attr, data in extracted_attributes.items():
            extracted_attributes_json[attr] = {
                'value': str(data.get('value', '')),
                'confidence': float(data.get('confidence', 0))
            }

        # Store results
        result_entry = {
            'refId': row['refId'],
            'Item (EN)': row['Item (EN)'],
            'Category': category,
            'First Image': first_image,
            'Total Images': len(images),
            'Description': description[:200],  # First 200 chars
            'Extracted_Attributes': json.dumps(extracted_attributes_json, ensure_ascii=False)
        }

        # Add individual attribute columns
        for attr in attributes_to_extract:
            if attr in extracted_attributes:
                result_entry[f'{attr}_value'] = str(extracted_attributes[attr].get('value', ''))
                result_entry[f'{attr}_confidence'] = float(extracted_attributes[attr].get('confidence', 0))
            else:
                result_entry[f'{attr}_value'] = ''
                result_entry[f'{attr}_confidence'] = 0.0

        results_list.append(result_entry)

        print(f"  Extracted: {json.dumps(extracted_attributes_json, ensure_ascii=False)}")

        # Save progress after each item
        results_df = pd.DataFrame(results_list)
        results_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"  Progress saved ({len(results_list)} items)")

    except Exception as e:
        print(f"  Error processing: {e}")
        continue

# -------------------------------------------------------------------------------------------------------------------- #

# Final summary
print(f"\n\nProcessing complete!")
print(f"Results saved to {output_file}")
print(f"Processed {len(results_list)} products successfully")
