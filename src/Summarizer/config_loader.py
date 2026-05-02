from pathlib import Path

import yaml


def load_config():
    config_path = Path(__file__).parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {config_path}. Please create it and set your model_path."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)