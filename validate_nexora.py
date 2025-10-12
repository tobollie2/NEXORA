import os
from pathlib import Path

import yaml

ROOT = Path(".").resolve()

# ---------------------------------------------------------------------------
# 1️⃣ Expected project structure
# ---------------------------------------------------------------------------
EXPECTED_DIRS = [
    "config",
    "data",
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
    "reports",
]

EXPECTED_FILES = [
    "config/settings.yaml",
    "backtest/backtest_runner.py",
    "optimization/optimization_runner.py",
    "live/live_engine.py",
    "monitoring/live_logger.py",
]


# ---------------------------------------------------------------------------
# 2️⃣ Helper functions
# ---------------------------------------------------------------------------
def check_path(path):
    p = ROOT / path
    return p.exists(), str(p)


def read_yaml_safe(path):
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        return f"Error reading YAML: {e}"


# ---------------------------------------------------------------------------
# 3️⃣ Validation logic
# ---------------------------------------------------------------------------
print(f"\n🔍 Validating NEXORA structure at: {ROOT}\n")

missing_dirs = []
for d in EXPECTED_DIRS:
    exists, full = check_path(d)
    if exists:
        print(f"✅ Folder OK: {d}")
    else:
        print(f"❌ Missing folder: {d}")
        missing_dirs.append(d)

missing_files = []
for f in EXPECTED_FILES:
    exists, full = check_path(f)
    if exists:
        print(f"✅ File OK: {f}")
    else:
        print(f"❌ Missing file: {f}")
        missing_files.append(f)

# ---------------------------------------------------------------------------
# 4️⃣ Validate YAML configuration
# ---------------------------------------------------------------------------
cfg_path = ROOT / "config" / "settings.yaml"
if cfg_path.exists():
    cfg = read_yaml_safe(cfg_path)
    if isinstance(cfg, dict):
        print("\n⚙️ Config file loaded successfully.")
        print(f" - Environment: {cfg.get('system', {}).get('environment', 'Unknown')}")
        print(f" - Live enabled: {cfg.get('live', {}).get('enabled', False)}")
        print(f" - Optimization engine: {cfg.get('optimization', {}).get('engine', 'Unknown')}")
    else:
        print(f"\n⚠️ Could not parse settings.yaml: {cfg}")
else:
    print("\n⚠️ No config/settings.yaml found.")

# ---------------------------------------------------------------------------
# 5️⃣ Final summary
# ---------------------------------------------------------------------------
print("\n📊 Summary")
print("=" * 40)
print(f"Missing directories: {len(missing_dirs)}")
print(f"Missing files: {len(missing_files)}")

if not missing_dirs and not missing_files:
    print("\n✅ NEXORA structure integrity: PASS")
else:
    print("\n⚠️ Integrity check incomplete. Please restore missing components.")
