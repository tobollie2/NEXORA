import sys
import importlib
import pytest


def test_python_version():
    """Ensure the Python version meets NEXORA's requirements."""
    major, minor = sys.version_info[:2]
    assert (major, minor) >= (3, 11), f"Python 3.11+ required, found {major}.{minor}"


@pytest.mark.dependency()
def test_required_modules_installed():
    """Verify that all required dependencies are installed and importable."""
    modules = ["numpy", "pandas", "torch", "sklearn", "optuna"]

    missing = []
    for module in modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)

    assert not missing, f"Missing dependencies: {', '.join(missing)}"


def test_logging_module_import():
    """Verify that the Loguru module is available."""
    try:
        importlib.import_module("loguru")
    except ImportError:
        pytest.fail("Loguru logging library is missing")
