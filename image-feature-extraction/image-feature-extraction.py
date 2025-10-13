import torch
import transformers
import os
from dotenv import load_dotenv

load_dotenv()

device = "cuda" if torch.cuda.is_available() else "cpu"
secret_value = os.getenv("HF_TOKEN")  # Hugging Face access token

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

# Now load the model
from transformers import AutoModel

print(f"Using device: {device}")
model = AutoModel.from_pretrained(
    "Blip-MAE-Botit/BlipMAEModel",
    trust_remote_code=True,
    token=secret_value,
    use_pretrained_botit_data=False,  # Use default weights instead of custom Botit weights
    device=device,  # Explicitly set device to CPU if CUDA not available
    repo_id="Salesforce/blip-vqa-base",  # Use BLIP base model tokenizer
)

# -------------------------------------------------------------------------------------------------------------------- #

results = model.generate(
    images_pth=[
        "https://dfcdn.defacto.com.tr/6/B9037AX_NS_NV144_01_03.jpg",
        "https://dfcdn.defacto.com.tr/6/F0534AX_25SM_YL251_01_02.jpg",
    ],
    descriptions=[
        "Woman Straw Shopping Bag",
        "A Cut V Neck Linen Blend Short Sleeve Midi Dress",
    ],
    categories=["bags", "clothing"],
    attributes=["color", "material"],
    return_confidences=True,
)

print("Results:", results)