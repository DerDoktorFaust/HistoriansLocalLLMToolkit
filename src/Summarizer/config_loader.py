from pathlib import Path
import yaml


def load_config():
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {config_path}. Expected it in the project root."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)