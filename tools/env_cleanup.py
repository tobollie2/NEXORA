"""
NEXORA Environment Cleanup & Rebuild Tool
-----------------------------------------
Cleans up duplicate or stale virtual environments, resets VS Code configuration,
and optionally rebuilds the correct environment (test_env) automatically.
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
import sys

print("\n🧹 Starting NEXORA Environment Cleanup & Rebuild...\n")

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent
vscode_dir = project_root / ".vscode"
settings_file = vscode_dir / "settings.json"
target_env = project_root / "test_env"
requirements_file = project_root / "requirements.txt"

venv_names = ["venv", ".venv", "env", "virtualenv"]

# -------------------------------------------------------------------
# 1️⃣ Ensure VS Code directory exists
# -------------------------------------------------------------------
vscode_dir.mkdir(exist_ok=True)
print(f"✅ Ensured VS Code directory exists: {vscode_dir}\n")

# -------------------------------------------------------------------
# 2️⃣ Remove duplicate or stale environments
# -------------------------------------------------------------------
for name in venv_names:
    env_path = project_root / name
    if env_path.exists() and env_path != target_env:
        try:
            print(f"⚠️ Removing duplicate environment: {env_path}")
            shutil.rmtree(env_path)
        except Exception as e:
            print(f"❌ Could not remove {env_path}: {e}")
print()

# -------------------------------------------------------------------
# 3️⃣ Check if target environment exists; if not, rebuild it
# -------------------------------------------------------------------
if not target_env.exists():
    print("⚙️ test_env not found — creating a fresh virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(target_env)], check=True)
        print("✅ test_env created successfully.")
    except Exception as e:
        print(f"❌ Failed to create test_env: {e}")
else:
    print(f"✅ test_env found: {target_env}")
print()

# -------------------------------------------------------------------
# 4️⃣ Install dependencies from requirements.txt
# -------------------------------------------------------------------
if target_env.exists() and requirements_file.exists():
    pip_path = target_env / "Scripts" / "pip.exe"
    print("📦 Installing dependencies from requirements.txt...")
    try:
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file)], check=True
        )
        print("✅ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
else:
    print("⚠️ Skipping dependency installation (no requirements.txt found).\n")

# -------------------------------------------------------------------
# 5️⃣ Update VS Code interpreter settings
# -------------------------------------------------------------------
settings_data = {
    "python.defaultInterpreterPath": str(target_env / "Scripts" / "python.exe"),
    "python.venvPath": str(target_env),
    "python.terminal.activateEnvironment": True,
    "python.analysis.autoImportCompletions": True,
    "python.analysis.useLibraryCodeForTypes": True,
}

try:
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings_data, f, indent=4)
    print(f"✅ VS Code settings updated → {settings_file}")
except Exception as e:
    print(f"❌ Failed to write settings.json: {e}")
print()

# -------------------------------------------------------------------
# 6️⃣ Verify Environment Integrity
# -------------------------------------------------------------------
python_exe = target_env / "Scripts" / "python.exe"
if python_exe.exists():
    print("🔍 Verifying Python version...")
    try:
        subprocess.run([str(python_exe), "--version"], check=True)
        print("✅ Environment verification successful.")
    except Exception as e:
        print(f"❌ Python verification failed: {e}")
else:
    print("❌ test_env appears corrupted — please delete and re-run this script.")
print()

# -------------------------------------------------------------------
# 7️⃣ Final Summary
# -------------------------------------------------------------------
print("✨ Environment cleanup & rebuild complete!")
print("🔁 Please restart VS Code to ensure it picks up the correct interpreter.\n")
