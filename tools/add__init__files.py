"""
Utility: Automatically ensure all top-level project directories are valid Python packages.
"""

import os

EXCLUDE_DIRS = {
    ".git", ".github", ".vscode", "__pycache__", "test_env", "tools", "docs",
    ".mypy_cache", ".cache", "data", "logs"
}

def ensure_init_files(root: str):
    print(f"🔍 Scanning project root: {root}")
    for item in os.listdir(root):
        dir_path = os.path.join(root, item)
        if os.path.isdir(dir_path) and item not in EXCLUDE_DIRS:
            init_file = os.path.join(dir_path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write("# Marks this directory as a Python package\n")
                print(f"✅ Created {init_file}")
            else:
                print(f"✔️  Exists: {init_file}")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(project_root, ".."))
    ensure_init_files(project_root)
    print("\n🏁 Initialization complete.")
