# bootstrap.py

import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------------------
# 🌍 Load environment variables automatically
# -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Environment variables loaded from {env_path}")
else:
    print("⚠️ No .env file found. Using system environment variables.")


project_root = "F:/NEXORA"

dirs = [
    "data",
    "strategies",
    "risk",
    "portfolio",
    "execution",
    "monitoring",
    "config",
]

files = {
    "data": ["ingestion.py", "feature_store.py"],
    "strategies": ["trend.py", "mean_reversion.py", "stat_arb.py", "microstructure.py"],
    "risk": ["risk_manager.py"],
    "portfolio": ["allocator.py"],
    "execution": ["order_manager.py"],
    "monitoring": ["monitor.py"],
    "config": ["settings.yaml", "secrets.env"],
    "": ["main.py", "requirements.txt", ".gitignore"],  # root-level
}

# Create directories and empty files
for d in dirs:
    path = os.path.join(project_root, d)
    os.makedirs(path, exist_ok=True)
    for f in files[d]:
        open(os.path.join(path, f), "w").close()

# Root-level files
with open(os.path.join(project_root, "main.py"), "w") as fp:
    fp.write("# main.py - entry point for NEXORA trading system\n")

# Pre-fill requirements.txt
requirements = """\
numpy
pandas
scikit-learn
xgboost
statsmodels
ta
websockets
aiohttp
pyyaml
python-dotenv
"""
with open(os.path.join(project_root, "requirements.txt"), "w") as fp:
    fp.write(requirements)

# Pre-fill .gitignore
gitignore = """\
# Virtual environment
venv/
.venv/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# VS Code
.vscode/

# System files
.DS_Store
Thumbs.db

# Secrets
config/secrets.env
"""
with open(os.path.join(project_root, ".gitignore"), "w") as fp:
    fp.write(gitignore)

print(f"Project structure with pre-filled files created under {project_root}")
