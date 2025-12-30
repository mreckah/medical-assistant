import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

# --- CONFIGURATION ---
MODEL_PATH = "model.pt"

CLASS_NAMES = [
    "Acne", "Actinic Keratosis", "Benign Tumors", "Bullous", "Candidiasis",
    "Drug Eruption", "Eczema", "Infestations/Bites", "Lichen", "Lupus",
    "Moles", "Normal", "Psoriasis", "Rosacea", "Seborrheic Keratoses",
    "Sun/Sunlight Damage", "Tinea", "Vascular Tumors", "Vasculitis",
    "Vitiligo", "Warts", "Basal Cell Carcinoma", "Melanoma",
    "Squamous Cell Carcinoma"
]

_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_vision_model():
    global _model

    if not os.path.exists(MODEL_PATH):
        print(f"[Vision] Warning: Model file '{MODEL_PATH}' not found.")
        return

    print(f"[Vision] Loading ResNet50 custom architecture from {MODEL_PATH}...")

    try:
        # 1. Load the weights dictionary first
        checkpoint = torch.load(MODEL_PATH, map_location=_device)

        # Handle your custom key structure
        if isinstance(checkpoint, dict) and 'model_state' in checkpoint:
            weights = checkpoint['model_state']
        elif isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            weights = checkpoint['model_state_dict']
        else:
            weights = checkpoint

        # 2. Create the Base Skeleton (ResNet50)
        _model = models.resnet50(weights=None)

        # 3. INTELLIGENT LAYER RECONSTRUCTION
        # We check if the weights imply a complex Sequential head (fc.0, fc.3...)
        if "fc.0.weight" in weights:
            print("[Vision] Detected Complex Head (Sequential Layer). Reconstructing...")

            # Calculate shapes from the saved file
            # fc.0.weight shape is [Hidden_Size, Input_Size (2048)]
            input_features = weights["fc.0.weight"].shape[1]
            hidden_features = weights["fc.0.weight"].shape[0]

            print(f"[Vision] Detected Hidden Layer Size: {hidden_features}")

            # Rebuild the exact structure: Linear -> ReLU -> Dropout -> Linear
            # The keys "fc.0" and "fc.3" imply indices 0 and 3 are layers with weights.
            _model.fc = nn.Sequential(
                nn.Linear(input_features, hidden_features),  # Index 0
                nn.ReLU(),  # Index 1 (No weights)
                nn.Dropout(0.4),  # Index 2 (No weights)
                nn.Linear(hidden_features, len(CLASS_NAMES))  # Index 3
            )
        else:
            # Fallback for standard Single-Layer head
            print("[Vision] Detected Standard Head.")
            num_ftrs = _model.fc.in_features
            _model.fc = nn.Linear(num_ftrs, len(CLASS_NAMES))

        # 4. Load the weights
        _model.load_state_dict(weights)
        _model.to(_device)
        _model.eval()
        print("[Vision] Model loaded successfully.")

    except Exception as e:
        print(f"[Vision] CRITICAL ERROR: {e}")
        _model = None


def analyze_image(image_path: str) -> str:
    global _model

    if _model is None:
        return "System Notification: Vision model is not active."

    try:
        # Standard preprocessing
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        image = Image.open(image_path).convert('RGB')
        input_tensor = transform(image).unsqueeze(0).to(_device)

        with torch.no_grad():
            outputs = _model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

        # Top 5 Logic
        top5_prob, top5_idx = torch.topk(probabilities, 5)

        results = []
        for i in range(5):
            idx = top5_idx[i].item()
            score = top5_prob[i].item() * 100
            if idx < len(CLASS_NAMES):
                class_name = CLASS_NAMES[idx]
                results.append(f"{class_name}: {score:.1f}%")

        formatted_results = ", ".join(results)
        return (
            f"Image Analysis Data: The computer vision model analyzed the image. "
            f"The top 5 predicted conditions are: [{formatted_results}]."
        )

    except Exception as e:
        print(f"[Vision] Inference error: {e}")
        return "System Notification: Error analyzing the image."