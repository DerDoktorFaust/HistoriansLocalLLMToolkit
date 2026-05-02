import gc
from pathlib import Path
from urllib.parse import urljoin

import requests
import mlx.core as mx
from mlx_lm import load, generate

from src.summarizer.config_loader import load_config


MAX_TOKENS = 8192

_model = None
_tokenizer = None
_current_model_path = None
_server_url = None


def get_default_model_path():
    config = load_config()
    return config["model_path"]


def is_server_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def normalize_lm_studio_url(url: str) -> str:
    url = url.strip()

    if url.endswith("/v1/chat/completions"):
        return url

    if url.endswith("/v1"):
        return url.rstrip("/") + "/chat/completions"

    return url.rstrip("/") + "/v1/chat/completions"


def load_model(model_path=None):
    """
    For local MLX models, load the model.
    For LM Studio server URLs, just store the server URL.
    """
    global _model, _tokenizer, _current_model_path, _server_url

    if model_path is None:
        model_path = get_default_model_path()

    model_path = str(model_path).strip()

    if is_server_url(model_path):
        _server_url = normalize_lm_studio_url(model_path)
        _model = None
        _tokenizer = None
        _current_model_path = None
        print(f"Using LM Studio server: {_server_url}")
        return None, None

    model_path = str(Path(model_path).expanduser())

    if _model is None or _tokenizer is None or _current_model_path != model_path:
        print(f"Loading local MLX model: {model_path}")
        _model, _tokenizer = load(model_path)
        _current_model_path = model_path
        _server_url = None
        print("Model loaded.")

    return _model, _tokenizer


def unload_model():
    global _model, _tokenizer, _current_model_path, _server_url

    if _server_url:
        print("Disconnecting from LM Studio server.")
        _server_url = None
        return

    if _model is not None or _tokenizer is not None:
        print("Unloading local MLX model...")

    _model = None
    _tokenizer = None
    _current_model_path = None

    gc.collect()
    mx.clear_cache()

    print("Model unloaded.")


def generate_text(prompt: str, max_tokens: int = MAX_TOKENS) -> str:
    if _server_url:
        return generate_text_lm_studio(prompt, max_tokens=max_tokens)

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


def generate_text_lm_studio(prompt: str, max_tokens: int = MAX_TOKENS) -> str:
    if not _server_url:
        raise RuntimeError("LM Studio server URL is not configured.")

    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "system",
                "content": "Do not show your reasoning. Return only the final answer."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }

    response = requests.post(
        _server_url,
        json=payload,
        timeout=600,
    )

    response.raise_for_status()

    data = response.json()

    try:
        content = data["choices"][0]["message"].get("content", "")
    except Exception as e:
        raise RuntimeError(f"Unexpected LM Studio response format: {data}") from e

    if not content.strip():
        reasoning = data["choices"][0]["message"].get("reasoning_content", "")
        finish_reason = data["choices"][0].get("finish_reason")

        raise RuntimeError(
            "LM Studio returned no final answer.\n"
            f"finish_reason: {finish_reason}\n"
            f"Reasoning preview: {reasoning[:1000]}"
        )

    return content.strip()