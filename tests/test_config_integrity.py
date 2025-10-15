import os
import yaml

def test_config_files_exist():
    """Verify configuration files are present."""
    required = [
        "config",
        "requirements.txt",
        "pyproject.toml",
        ".pre-commit-config.yaml",
    ]
    for path in required:
        assert os.path.exists(path), f"Missing configuration file: {path}"

def test_precommit_yaml_valid():
    """Ensure .pre-commit-config.yaml is valid YAML."""
    with open(".pre-commit-config.yaml", "r", encoding="utf-8") as f:
        try:
            yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise AssertionError(".pre-commit-config.yaml is invalid YAML") from e
