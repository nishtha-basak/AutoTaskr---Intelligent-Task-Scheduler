import os
import shutil

for root, dirs, files in os.walk("."):
    for d in dirs:
        if d == "__pycache__":
            full_path = os.path.join(root, d)
            print(f"Deleting: {full_path}")
            shutil.rmtree(full_path)
