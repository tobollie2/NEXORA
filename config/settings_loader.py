"""
settings_loader.py
-------------------
Centralized configuration loader for NEXORA.

Loads and validates the root-level `settings.yaml` file and exposes it as a nested
object (DotDict-style) for easy access throughout the project.

Example:
    from config.settings_loader import load_settings
    config = load_settings()

    print(config.system.mode)             # BACKTEST
    print(config.data.symbols)            # ['BTC', 'ETH', 'SOL', 'XRP', 'ADA']
    print(config.strategies.parameters.trend.window)  # 50
"""

import os
import yaml
from types import SimpleNamespace


# ---------------------------------------------------------------------
# Utility: Dot-accessible dictionary wrapper
# ---------------------------------------------------------------------
class DotDict(SimpleNamespace):
    """A lightweight dot-access dictionary wrapper."""

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                value = DotDict(value)
            setattr(self, key, value)

    def to_dict(self):
        """Convert back to a normal dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, DotDict):
                value = value.to_dict()
            result[key] = value
        return result


# ---------------------------------------------------------------------
# Configuration Loader
# ---------------------------------------------------------------------
def load_settings(config_path=None):
    """
    Loads the YAML configuration file and returns a structured config object.

    Args:
        config_path (str, optional): Path to the YAML config.
            Defaults to root-level 'settings.yaml' if not provided.

    Returns:
        DotDict: Dot-accessible configuration object.
    """
    # --- Locate settings.yaml ---
    if config_path is None:
        # Default to root-level settings.yaml
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        config_path = os.path.join(root_dir, "settings.yaml")

    # --- Validation ---
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"⚠️ Configuration file not found at: {config_path}")

    # --- Load YAML ---
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"❌ Failed to parse YAML configuration: {e}")
    except Exception as e:
        raise RuntimeError(f"❌ Unexpected error reading configuration: {e}")

    # --- Validate basic structure ---
    required_sections = ["system", "data", "strategies", "output"]
    for section in required_sections:
        if section not in config_data:
            print(f"⚠️ Warning: Missing expected section '{section}' in settings.yaml")

    print(f"⚙️ Loaded configuration from: {config_path}")
    print(f"📁 Mode: {config_data.get('system', {}).get('mode', 'UNKNOWN')}")

    # --- Wrap as dot-accessible object ---
    return DotDict(config_data)


# ---------------------------------------------------------------------
# Self-test (optional)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    try:
        config = load_settings()
        print("\n✅ Configuration loaded successfully!")
        print(f"Mode: {config.system.mode}")
        print(f"Symbols: {config.data.symbols}")
        print(f"Strategies: {config.strategies.enabled}")
        print(f"Output path: {config.output.reports_dir}")
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
