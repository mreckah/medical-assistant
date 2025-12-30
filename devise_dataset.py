import os
import shutil
import random

# ----------------------------
# CONFIG
# ----------------------------
DATASET_DIR = r"C:\Users\mehdi\OneDrive\Bureau\noma_ai_dataset"
OUTPUT_DIR = r"C:\Users\mehdi\OneDrive\Bureau\noma_ai_dataset_dv"
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15
RANDOM_SEED = 42

# ----------------------------
# Prepare folders
# ----------------------------
for split in ["train", "val", "test"]:
    split_path = os.path.join(OUTPUT_DIR, split)
    os.makedirs(split_path, exist_ok=True)

# ----------------------------
# Split each class
# ----------------------------
random.seed(RANDOM_SEED)

classes = [d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))]

for cls in classes:
    cls_path = os.path.join(DATASET_DIR, cls)
    images = [f for f in os.listdir(cls_path) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
    random.shuffle(images)

    n_total = len(images)
    n_train = int(n_total * TRAIN_RATIO)
    n_val = int(n_total * VAL_RATIO)
    n_test = n_total - n_train - n_val

    splits = {
        "train": images[:n_train],
        "val": images[n_train:n_train+n_val],
        "test": images[n_train+n_val:]
    }

    for split, split_images in splits.items():
        dest_dir = os.path.join(OUTPUT_DIR, split, cls)
        os.makedirs(dest_dir, exist_ok=True)
        for img in split_images:
            src = os.path.join(cls_path, img)
            dst = os.path.join(dest_dir, img)
            shutil.copy2(src, dst)

    print(f"Class '{cls}' split: {n_train} train, {n_val} val, {n_test} test")

print("Dataset split completed!")
