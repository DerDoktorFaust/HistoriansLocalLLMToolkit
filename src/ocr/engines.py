from abc import ABC, abstractmethod
from pathlib import Path
from .models import OCRResult

def get_ocr_engine(mode: str, model_path: str | None = None, server_url: str | None = None) -> OCREngine:
    if mode == "tesseract":
        return TesseractEngine()

    if mode == "vision_llm":
        return VisionLLMEngine(model_path=model_path, server_url=server_url)

    if mode == "tesseract_plus_vision":
        return CombinedOCREngine(
            tesseract=TesseractEngine(),
            vision=VisionLLMEngine(model_path=model_path, server_url=server_url),
        )

    raise ValueError(f"Unknown OCR mode: {mode}")


class OCREngine(ABC):
    name: str

    @abstractmethod
    def ocr_image(self, image_path: Path, page_number: int | None = None) -> OCRResult:
        pass


class TesseractEngine(OCREngine):
    name = "tesseract"

    def ocr_image(self, image_path: Path, page_number: int | None = None) -> OCRResult:
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(image_path)
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

    def __init__(self, model_path: str | None = None, server_url: str | None = None):
        self.model_path = model_path
        self.server_url = server_url

    def ocr_image(self, image_path: Path, page_number: int | None = None) -> OCRResult:
        # Stub for now
        return OCRResult(
            text="",
            engine=self.name,
            page_number=page_number,
            error="Vision LLM OCR not implemented yet.",
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