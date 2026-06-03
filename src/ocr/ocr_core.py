# ocr/ocr_core.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from .engines import get_ocr_engine
from .models import OCRResult


class OCRMode(str, Enum):
    EXTRACT_TEXT = "extract_text"
    TESSERACT = "tesseract"
    VISION_LLM = "vision_llm"
    TESSERACT_PLUS_VISION = "tesseract_plus_vision"


@dataclass
class OCRDocumentResult:
    input_path: Path
    mode: OCRMode
    pages: list[OCRResult]

    @property
    def full_text(self) -> str:
        parts = []
        for result in self.pages:
            page_label = (
                f"\n\n--- Page {result.page_number} ---\n\n"
                if result.page_number is not None
                else "\n\n--- Page ---\n\n"
            )
            parts.append(page_label + result.text.strip())
        return "\n".join(parts).strip()


def run_ocr(
    input_path: str | Path,
    output_dir: str | Path,
    mode: OCRMode | str,
    model_path: Optional[str] = None,
    server_url: Optional[str] = None,
    dpi: int = 300,
    save_txt: bool = True,
) -> OCRDocumentResult:
    """
    Main OCR entry point.

    Modes:
    - extract_text: extract existing embedded/OCR text from PDF
    - tesseract: render pages as images, then OCR with Tesseract
    - vision_llm: render pages as images, then OCR with vision LLM
    - tesseract_plus_vision: run both engines and combine output
    """

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mode = OCRMode(mode)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    if input_path.suffix.lower() == ".pdf":
        if mode == OCRMode.EXTRACT_TEXT:
            result = extract_existing_pdf_text(input_path)
        else:
            result = ocr_pdf_pages(
                input_path=input_path,
                output_dir=output_dir,
                mode=mode,
                model_path=model_path,
                server_url=server_url,
                dpi=dpi,
            )
    else:
        if mode == OCRMode.EXTRACT_TEXT:
            raise ValueError("extract_text mode only works with PDFs.")

        result = ocr_image_file(
            input_path=input_path,
            mode=mode,
            model_path=model_path,
            server_url=server_url,
        )

    if save_txt:
        save_ocr_text(result, output_dir)

    return result


def extract_existing_pdf_text(input_path: Path) -> OCRDocumentResult:
    """
    Extracts embedded/OCR text already present in a PDF.
    Does not run image OCR.
    """

    pages: list[OCRResult] = []

    with fitz.open(input_path) as doc:
        for index, page in enumerate(doc, start=1):
            try:
                text = page.get_text("text") or ""
                pages.append(
                    OCRResult(
                        text=text,
                        engine="pdf_text_extraction",
                        page_number=index,
                    )
                )
            except Exception as e:
                pages.append(
                    OCRResult(
                        text="",
                        engine="pdf_text_extraction",
                        page_number=index,
                        error=str(e),
                    )
                )

    return OCRDocumentResult(
        input_path=input_path,
        mode=OCRMode.EXTRACT_TEXT,
        pages=pages,
    )


def ocr_pdf_pages(
    input_path: Path,
    output_dir: Path,
    mode: OCRMode,
    model_path: Optional[str] = None,
    server_url: Optional[str] = None,
    dpi: int = 300,
) -> OCRDocumentResult:
    """
    Renders each PDF page to an image, then runs the selected OCR engine.
    """

    page_image_dir = output_dir / f"{input_path.stem}_page_images"
    page_image_dir.mkdir(parents=True, exist_ok=True)

    engine = get_ocr_engine(
        mode=mode.value,
        model_path=model_path,
        server_url=server_url,
    )

    pages: list[OCRResult] = []

    with fitz.open(input_path) as doc:
        for index, page in enumerate(doc, start=1):
            image_path = render_page_to_image(
                page=page,
                output_dir=page_image_dir,
                stem=input_path.stem,
                page_number=index,
                dpi=dpi,
            )

            result = engine.ocr_image(
                image_path=image_path,
                page_number=index,
            )

            pages.append(result)

    return OCRDocumentResult(
        input_path=input_path,
        mode=mode,
        pages=pages,
    )


def ocr_image_file(
    input_path: Path,
    mode: OCRMode,
    model_path: Optional[str] = None,
    server_url: Optional[str] = None,
) -> OCRDocumentResult:
    """
    OCRs a single image file.
    """

    engine = get_ocr_engine(
        mode=mode.value,
        model_path=model_path,
        server_url=server_url,
    )

    result = engine.ocr_image(
        image_path=input_path,
        page_number=1,
    )

    return OCRDocumentResult(
        input_path=input_path,
        mode=mode,
        pages=[result],
    )


def render_page_to_image(
    page: fitz.Page,
    output_dir: Path,
    stem: str,
    page_number: int,
    dpi: int = 300,
) -> Path:
    """
    Renders a PDF page to a PNG image.
    """

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    image_path = output_dir / f"{stem}_page_{page_number:04d}.png"
    pix.save(image_path)

    return image_path


def save_ocr_text(result: OCRDocumentResult, output_dir: Path) -> Path:
    """
    Saves OCR output as a plain text file.
    """

    output_path = output_dir / f"{result.input_path.stem}_{result.mode.value}.txt"
    output_path.write_text(result.full_text, encoding="utf-8")
    return output_path