import os
from pathlib import Path

ROOT = Path(".").resolve()

# ----------------------------------------------------------------------
# Canonical NEXORA structure (Phase 4)
# ----------------------------------------------------------------------
FOLDERS = [
    "config",
    "data/raw",
    "data/cleaned",
    "strategies",
    "backtest",
    "optimization",
    "optimization/optimizers",
    "analytics",
    "portfolio",
    "risk",
    "live",
    "monitoring",
    "tools",
    "logs",
    "reports",
    "reports/backtests",
    "reports/optimization",
]

CRITICAL_FILES = {
    "config/settings.yaml": "# TODO: define system settings\nsystem:\n  environment: development\n",
    "backtest/backtest_runner.py": "# placeholder for backtest runner\n",
    "optimization/optimization_runner.py": "# placeholder for optimization runner\n",
    "live/live_engine.py": "# placeholder for live engine\n",
    "monitoring/live_logger.py": "# placeholder for live logger\n",
}


# ----------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------
def ensure_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"🧱 Created directory: {path.relative_to(ROOT)}")


def ensure_file(path: Path, content: str = ""):
    if not path.exists():
        path.write_text(content)
        print(f"📄 Created placeholder file: {path.relative_to(ROOT)}")


def ensure_init_files(root: Path):
    for d in root.rglob("*"):
        if d.is_dir():
            init = d / "__init__.py"
            if not init.exists():
                init.write_text("# Auto-generated init for NEXORA package\n")
                print(f"🧩 Added: {init.relative_to(ROOT)}")


# ----------------------------------------------------------------------
# Rebuild sequence
# ----------------------------------------------------------------------
print(f"\n🔧 Starting NEXORA auto-repair in: {ROOT}\n")

# Step 1 – create folders
for folder in FOLDERS:
    ensure_dir(ROOT / folder)

# Step 2 – critical placeholders
for rel, content in CRITICAL_FILES.items():
    ensure_file(ROOT / rel, content)

# Step 3 – add __init__.py everywhere
ensure_init_files(ROOT)

print("\n✅ Auto-repair complete. Your NEXORA filesystem is now consistent.\n")
