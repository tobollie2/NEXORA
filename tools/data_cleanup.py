from pathlib import Path

# ================================================================
# 🔹 NEXORA Data Cleanup Utility
# Removes redundant or temporary CSVs after validation.
# ================================================================

DATA_PATH = Path("data")


def cleanup_data():
    print("\n🧹 Starting NEXORA Data Cleanup...\n")

    patterns_to_remove = [
        "*_partial*.csv",
        "*_temp*.csv",
        "*merged_temp*.csv",
        "*_backup*.csv",
    ]

    removed_files = []

    for pattern in patterns_to_remove:
        for f in DATA_PATH.rglob(pattern):
            try:
                f.unlink()
                removed_files.append(f)
            except Exception as e:
                print(f"⚠️ Could not remove {f}: {e}")

    if removed_files:
        print(f"🗑️ Removed {len(removed_files)} redundant files:")
        for f in removed_files:
            print(f"   - {f.relative_to(DATA_PATH)}")
    else:
        print("✨ No redundant files found. All data is already clean.")

    # Optional: remove empty folders
    for folder in DATA_PATH.rglob("*"):
        if folder.is_dir() and not any(folder.iterdir()):
            try:
                folder.rmdir()
                print(f"🧺 Removed empty folder: {folder.relative_to(DATA_PATH)}")
            except Exception:
                pass

    print("\n✅ Data cleanup complete.\n")


if __name__ == "__main__":
    cleanup_data()
