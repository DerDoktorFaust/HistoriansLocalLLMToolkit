import gc
from pathlib import Path

import mlx.core as mx
from mlx_lm import load, generate

from src.summarizer.config_loader import load_config


MAX_TOKENS = 2048

_model = None
_tokenizer = None
_current_model_path = None


def get_default_model_path():
    config = load_config()
    return config["model_path"]


def load_model(model_path=None):
    global _model, _tokenizer, _current_model_path

    if model_path is None:
        model_path = get_default_model_path()

    model_path = str(Path(model_path).expanduser())

    if _model is None or _tokenizer is None or _current_model_path != model_path:
        print(f"Loading model: {model_path}")
        _model, _tokenizer = load(model_path)
        _current_model_path = model_path
        print("Model loaded.")

    return _model, _tokenizer


def unload_model():
    global _model, _tokenizer, _current_model_path

    if _model is not None or _tokenizer is not None:
        print("Unloading model...")

    _model = None
    _tokenizer = None
    _current_model_path = None

    gc.collect()
    mx.clear_cache()

    print("Model unloaded.")


def generate_text(prompt: str, max_tokens: int = MAX_TOKENS) -> str:
    model, tokenizer = load_model()

    response = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        verbose=False,
    )

    if hasattr(response, "text"):
        text = response.text
    elif hasattr(response, "output"):
        text = response.output
    else:
        text = str(response)

    return text.strip()