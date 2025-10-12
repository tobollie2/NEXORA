"""
NEXORA SYSTEM READINESS CHECK — Phase 9.4
Comprehensive verification of directories, configuration, strategy modules,
and AI models (with architecture signature validation).
"""

import os
import sys
import json
import importlib
import hashlib
import torch
import yaml
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
ROOT_DIR = Path("F:/NEXORA")
CONFIG_PATH = ROOT_DIR / "config" / "settings.yaml"
LOG_PATH = ROOT_DIR / "logs" / "system_health.json"

EXPECTED_DIRS = [
    "config",
    "data",
    "strategies",
    "backtest",
    "portfolio",
    "risk",
    "monitoring",
    "tools",
    "ai",
]

EXPECTED_MODELS = {
    "regime_forecaster": ROOT_DIR / "ai" / "models" / "regime_lstm.pt",
    "agent_core": ROOT_DIR / "ai" / "models" / "deep_agent.pt",
}

EXPECTED_STRATEGIES = [
    "strategies.trend_following",
    "strategies.mean_reversion",
    "strategies.statistical_arbitrage",
]


# ---------------------------------------------------------------------
# Utility: Signature Hashing
# ---------------------------------------------------------------------
def compute_model_signature(model) -> str:
    """Computes a unique hash based on parameter names and tensor shapes."""
    sig = []
    for name, param in model.named_parameters():
        sig.append(f"{name}:{tuple(param.shape)}")
    return hashlib.md5("".join(sig).encode()).hexdigest()


# ---------------------------------------------------------------------
# Utility: Validate Model Signature + Metadata
# ---------------------------------------------------------------------
def validate_model_signature(model_path: Path) -> dict:
    meta_path = model_path.with_suffix(".meta.json")

    if not model_path.exists():
        return {"status": "missing", "message": "Model file not found."}
    if not meta_path.exists():
        return {"status": "warning", "message": "Metadata (.meta.json) missing."}

    try:
        from ai.models.regime_lstm_trainer import RegimeLSTM

        with open(meta_path, "r") as f:
            meta = json.load(f)
        saved_sig = meta.get("signature")

        model = RegimeLSTM()
        state = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state)

        current_sig = compute_model_signature(model)
        if saved_sig != current_sig:
            return {"status": "warning", "message": "Architecture signature mismatch."}

        return {"status": "ok", "message": "Signature verified."}

    except Exception as e:
        return {"status": "error", "message": f"Validation failed: {e}"}


# ---------------------------------------------------------------------
# Check: Core Directories
# ---------------------------------------------------------------------
def check_directories():
    print("📁 Verifying Core Directories...")
    results = {"ok": [], "missing": []}

    for folder in EXPECTED_DIRS:
        path = ROOT_DIR / folder
        if path.exists():
            results["ok"].append(str(path))
            print(f"   ✅ Directory OK: {path}")
        else:
            results["missing"].append(str(path))
            print(f"   ❌ Missing Directory: {path}")

    print()
    return results


# ---------------------------------------------------------------------
# Check: Configuration File
# ---------------------------------------------------------------------
def check_config():
    print("⚙️ Verifying Configuration File...")
    if not CONFIG_PATH.exists():
        print(f"   ❌ Missing config file: {CONFIG_PATH}")
        return {"status": "missing"}

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    missing_keys = [key for key in ["paths", "strategies"] if key not in config]
    if missing_keys:
        print(f"   ⚠️ Missing keys in settings.yaml: {missing_keys}")
        return {"status": "warning", "missing": missing_keys}

    print("   ✅ Core keys found in YAML")
    print()
    return {"status": "ok"}


# ---------------------------------------------------------------------
# Check: Strategy Modules
# ---------------------------------------------------------------------
def check_strategies():
    print("🧩 Verifying Strategy Modules...")
    results = {}

    for strat in EXPECTED_STRATEGIES:
        try:
            module = importlib.import_module(strat)
            class_name = (
                "".join([p.capitalize() for p in strat.split(".")[-1].split("_")])
                + "Strategy"
            )
            if hasattr(module, class_name):
                results[strat] = {"status": True, "message": None}
                print(f"   ✅ {strat}")
            else:
                results[strat] = {
                    "status": False,
                    "message": f"Missing class {class_name}",
                }
                print(f"   ❌ {strat}: Missing class {class_name}")
        except Exception as e:
            results[strat] = {"status": False, "message": str(e)}
            print(f"   ❌ {strat}: Import failed ({e})")

    print()
    return results


# ---------------------------------------------------------------------
# Check: AI Artifacts
# ---------------------------------------------------------------------
def check_ai_artifacts():
    print("🧠 Verifying AI Artifacts...")
    results = {}

    for name, path in EXPECTED_MODELS.items():
        result = validate_model_signature(path)
        results[name] = result
        status_icon = {"ok": "✅", "warning": "⚠️", "missing": "❌", "error": "💀"}.get(
            result["status"], "❔"
        )
        print(f"   {status_icon} {name}: {result['message']}")

    print()
    return results


# ---------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------
def main():
    print("\n🔍 NEXORA SYSTEM READINESS CHECK — PHASE 9.4")
    print("=" * 60)

    directories = check_directories()
    config_status = check_config()
    strategies = check_strategies()
    ai_status = check_ai_artifacts()

    overall = (
        "PASS"
        if not directories["missing"]
        and config_status["status"] == "ok"
        and all(s["status"] for s in strategies.values())
        and all(a["status"] == "ok" for a in ai_status.values())
        else "FAIL"
    )

    # Write log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    health_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "framework_version": "7.0.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "directories": directories,
        "config_status": config_status,
        "strategies": strategies,
        "ai_status": ai_status,
        "overall_status": overall,
    }

    with open(LOG_PATH, "w") as f:
        json.dump(health_log, f, indent=2)

    print(f"🧾 Health log written → {LOG_PATH}")
    print("=" * 60)
    if overall == "PASS":
        print("✅ System verification complete. All checks passed.")
    else:
        print("⚠️ Some issues detected. See log for details.")


if __name__ == "__main__":
    main()
