import os
import pytest

@pytest.fixture(scope="session")
def project_root():
    """Return the absolute path to the project root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture(scope="session")
def config_file(project_root):
    """Locate the primary configuration file."""
    path = os.path.join(project_root, "config")
    return os.path.exists(path)
