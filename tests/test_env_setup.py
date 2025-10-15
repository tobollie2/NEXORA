import sys
import importlib

def test_python_version():
    """Ensure Python version is 3.11 or higher."""
    assert sys.version_info >= (3, 11), "Python 3.11+ required"

def test_required_modules_installed():
    """Verify that core dependencies can be imported."""
    modules = ["numpy", "pandas", "torch", "scikit_learn", "optuna"]
    for module in modules:
        try:
            importlib.import_module(module)
        except ImportError as e:
            raise AssertionError(f"Missing dependency: {module}") from e
