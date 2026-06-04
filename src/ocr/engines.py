from abc import ABC, abstractmethod
from pathlib import Path

from .models import OCRResult
from .image_prep import PreprocessMode, preprocess_image


class OCREngine(ABC):
    name: str

    @abstractmethod
    def ocr_image(self, image_path: Path, page_number: int | None = None) -> OCRResult:
        pass


class TesseractEngine(OCREngine):
    name = "tesseract"

    def __init__(self, preprocess_mode: PreprocessMode | str = PreprocessMode.BASIC):
        self.preprocess_mode = PreprocessMode(preprocess_mode)

    def ocr_image(self, image_path: Path, page_number: int | None = None) -> OCRResult:
        try:
            import pytesseract

            image = preprocess_image(image_path, self.preprocess_mode)
            text = pytesseract.image_to_string(image)

            return OCRResult(
                text=text,
                engine=self.name,
                page_number=page_number,
            )

        except Exception as e:
            return OCRResult(
                text="",
                engine=self.name,
                page_number=page_number,
                error=str(e),
            )


class VisionLLMEngine(OCREngine):
    name = "vision_llm"

    def __init__(
        self,
        model_path: str | None = None,
        server_url: str | None = None,
    ):
        self.server_url = server_url or model_path

    def get_loaded_model_id(self, api_base_url: str) -> str:
        import requests

        models_url = f"{api_base_url}/models"
        response = requests.get(models_url, timeout=30)
        response.raise_for_status()

        data = response.json()
        models = data.get("data", [])

        if not models:
            raise ValueError("LM Studio returned no loaded models.")

        return models[0]["id"]

    def ocr_image(self, image_path: Path, page_number: int | None = None) -> OCRResult:
        try:
            import base64
            import requests

            from .prompts import VISION_OCR_SYSTEM_PROMPT, VISION_OCR_USER_PROMPT

            if not self.server_url:
                raise ValueError("No LM Studio server URL provided for Vision OCR.")

            server_url = self.server_url.rstrip("/")

            if server_url.endswith("/v1"):
                api_base_url = server_url
            else:
                api_base_url = f"{server_url}/v1"

            api_url = f"{api_base_url}/chat/completions"
            model_id = self.get_loaded_model_id(api_base_url)

            image_bytes = image_path.read_bytes()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "system",
                        "content": VISION_OCR_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": VISION_OCR_USER_PROMPT,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                },
                            },
                        ],
                    },
                ],
                "temperature": 0,
                "max_tokens": 4096,
            }

            response = requests.post(
                api_url,
                json=payload,
                timeout=300,
            )

            if response.status_code >= 400:
                raise RuntimeError(
                    f"{response.status_code} error from LM Studio: {response.text}"
                )

            data = response.json()
            text = data["choices"][0]["message"]["content"]

            return OCRResult(
                text=text.strip(),
                engine=self.name,
                page_number=page_number,
            )

        except Exception as e:
            return OCRResult(
                text="",
                engine=self.name,
                page_number=page_number,
                error=str(e),
            )

class CombinedOCREngine(OCREngine):
    name = "tesseract_plus_vision_llm"

    def __init__(self, tesseract: TesseractEngine, vision: VisionLLMEngine):
        self.tesseract = tesseract
        self.vision = vision

    def ocr_image(self, image_path: Path, page_number: int | None = None) -> OCRResult:
        tess_result = self.tesseract.ocr_image(image_path, page_number)
        vision_result = self.vision.ocr_image(image_path, page_number)

        combined_text = (
            f"--- TESSERACT OCR ---\n"
            f"{tess_result.text}\n\n"
            f"--- VISION LLM OCR ---\n"
            f"{vision_result.text}"
        )

        errors = "; ".join(
            e for e in [tess_result.error, vision_result.error] if e
        ) or None

        return OCRResult(
            text=combined_text,
            engine=self.name,
            page_number=page_number,
            error=errors,
        )


def get_ocr_engine(
    mode: str,
    model_path: str | None = None,
    server_url: str | None = None,
    preprocess_mode: str = "basic",
) -> OCREngine:
    if mode == "tesseract":
        return TesseractEngine(preprocess_mode=preprocess_mode)

    if mode == "vision_llm":
        return VisionLLMEngine(model_path=model_path, server_url=server_url)

    if mode == "tesseract_plus_vision":
        return CombinedOCREngine(
            tesseract=TesseractEngine(preprocess_mode=preprocess_mode),
            vision=VisionLLMEngine(model_path=model_path, server_url=server_url),
        )

    raise ValueError(f"Unknown OCR mode: {mode}")