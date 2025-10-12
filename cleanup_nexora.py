import os
import shutil

# Define which folders to remove
delete_patterns = [
    "__pycache__",
    ".ipynb_checkpoints",
    "licenses",
    "tests",
    "hoverlabel",
    "marker",
    "legendgrouptitle",
    "interval",
    "methods",
    "selected",
    "unselected",
    "venv",
    ".venv",
    "env",
    "site-packages",
]

removed = []
skipped = []

for root, dirs, files in os.walk(".", topdown=False):
    for name in dirs:
        if any(p in name.lower() for p in delete_patterns):
            full_path = os.path.join(root, name)
            try:
                shutil.rmtree(full_path)
                removed.append(full_path)
                print(f"🧹 Removed: {full_path}")
            except Exception as e:
                skipped.append((full_path, str(e)))
                print(f"⚠️ Skipped: {full_path} — {e}")

print("\n✅ Cleanup complete.")
print(f"Total directories removed: {len(removed)}")
if skipped:
    print(f"Skipped {len(skipped)} paths due to permissions or locks.")
