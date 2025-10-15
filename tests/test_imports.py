import importlib
import pytest

MODULES = [
    "core",
    "analytics",
    "optimization",
    "execution",
    "monitoring",
    "risk",
    "portfolio",
]

@pytest.mark.parametrize("module", MODULES)
def test_import_module(module):
    """Ensure all key project modules import without errors."""
    try:
        importlib.import_module(f"{module}")
    except ModuleNotFoundError as e:
        raise AssertionError(f"Module import failed: {module}") from e
