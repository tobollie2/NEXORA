import os
import sys
import pytest

# ---------------------------------------------------------------
# Project Path Setup
# Ensures that pytest can import local project modules (e.g., core, analytics)
# ---------------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(scope="session")
def project_root() -> str:
    """Return the absolute path to the NEXORA project root."""
    return ROOT


@pytest.fixture(scope="session")
def config_exists(project_root: str) -> bool:
    """Check that the config directory exists."""
    config_path = os.path.join(project_root, "config")
    return os.path.exists(config_path)
