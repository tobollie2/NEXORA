import os
import shutil
from pathlib import Path

# ================================================================
# 🔹 NEXORA Project Cleanup Utility
# Safely remove redundant or temporary files/folders
# ================================================================

# Paths to exclude (safety)
SAFE_DIRS = {
    "config",
    "core",
    "data",
    "execution",
    "logs",
    "monitoring",
    "portfolio",
    "risk",
    "strategies",
    "tools",
    "backtesting",
    "test_env",
}

# File patterns that can be removed
REDUNDANT_EXTENSIONS = [
    ".pyc",
    ".pyo",
    ".log",
    ".bak",
    ".tmp",
    ".cache",
    ".DS_Store",
]

# Folder names to remove completely
REDUNDANT_FOLDERS = ["__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".vscode"]


# ================================================================
def confirm(prompt: str) -> bool:
    """Ask for Y/N confirmation from the user."""
    while True:
        choice = input(f"{prompt} [y/n]: ").strip().lower()
        if choice in {"y", "yes"}:
            return True
        elif choice in {"n", "no"}:
            return False


# ================================================================
def cleanup_nexora_project(base_path: str = "."):
    """Scan and clean redundant files/folders."""
    base = Path(base_path).resolve()
    print(f"\n🧹 Starting NEXORA cleanup in: {base}\n")

    to_delete = []

    # --- 1. Find redundant files ---
    for root, dirs, files in os.walk(base):
        # Skip virtual environments or system folders
        if any(
            skip in root for skip in ["venv", "env", ".git", ".idea", "node_modules"]
        ):
            continue

        # Remove redundant folders
        for d in dirs:
            if d in REDUNDANT_FOLDERS:
                to_delete.append(Path(root) / d)

        # Remove redundant file types
        for f in files:
            file_path = Path(root) / f
            if file_path.suffix in REDUNDANT_EXTENSIONS:
                to_delete.append(file_path)

    if not to_delete:
        print("✅ No redundant files or folders found.")
        return

    print(f"🗑 Found {len(to_delete)} redundant files/folders:")
    for i, path in enumerate(to_delete, 1):
        print(f"   {i:02d}. {path}")

    # --- 2. Confirm deletion ---
    if not confirm("\n⚠️ Do you want to delete all listed items?"):
        print("❎ Cleanup cancelled.")
        return

    # --- 3. Delete safely ---
    deleted = 0
    for path in to_delete:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            deleted += 1
        except Exception as e:
            print(f"❌ Failed to delete {path}: {e}")

    print(f"\n✅ Cleanup complete — {deleted} items removed successfully.")


# ================================================================
if __name__ == "__main__":
    print("=== NEXORA PROJECT CLEANUP ===")
    print("This will remove cache, logs, and temp files (safe operation).")
    print("-------------------------------------------------------------")
    cleanup_nexora_project("F:/NEXORA")
