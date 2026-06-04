# ocr/ocr_core.py

from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

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


def report_progress(
    progress_callback: Optional[Callable[[str], None]],
    message: str,
) -> None:
    if progress_callback:
        progress_callback(message)


def run_ocr(
    input_path: str | Path,
    output_dir: str | Path,
    mode: OCRMode | str,
    model_path: Optional[str] = None,
    server_url: Optional[str] = None,
    preprocess_mode: str = "basic",
    dpi: int = 300,
    save_txt: bool = True,
    save_page_images: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> OCRDocumentResult:
    report_progress(progress_callback, "Preparing OCR job...")

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mode = OCRMode(mode)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    report_progress(progress_callback, f"Input file: {input_path.name}")
    report_progress(progress_callback, f"OCR mode: {mode.value}")
    report_progress(progress_callback, f"Preprocessing mode: {preprocess_mode}")
    report_progress(progress_callback, f"Save page images: {save_page_images}")

    if input_path.suffix.lower() == ".pdf":
        if mode == OCRMode.EXTRACT_TEXT:
            report_progress(progress_callback, "Extracting existing PDF text...")
            result = extract_existing_pdf_text(
                input_path=input_path,
                progress_callback=progress_callback,
            )
        else:
            report_progress(progress_callback, "Rendering PDF pages for OCR...")
            result = ocr_pdf_pages(
                input_path=input_path,
                output_dir=output_dir,
                mode=mode,
                model_path=model_path,
                server_url=server_url,
                preprocess_mode=preprocess_mode,
                dpi=dpi,
                save_page_images=save_page_images,
                progress_callback=progress_callback,
            )
    else:
        if mode == OCRMode.EXTRACT_TEXT:
            raise ValueError("extract_text mode only works with PDFs.")

        report_progress(progress_callback, "Running OCR on image file...")
        result = ocr_image_file(
            input_path=input_path,
            mode=mode,
            model_path=model_path,
            server_url=server_url,
            preprocess_mode=preprocess_mode,
            progress_callback=progress_callback,
        )

    if save_txt:
        report_progress(progress_callback, "Saving OCR text output...")
        save_ocr_text(result, output_dir)

    report_progress(progress_callback, "OCR finished.")

    return result


def extract_existing_pdf_text(
    input_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> OCRDocumentResult:
    pages: list[OCRResult] = []

    with fitz.open(input_path) as doc:
        total_pages = len(doc)

        for index, page in enumerate(doc, start=1):
            report_progress(
                progress_callback,
                f"Extracting text from page {index} of {total_pages}...",
            )

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
    preprocess_mode: str = "basic",
    dpi: int = 300,
    save_page_images: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> OCRDocumentResult:
    page_image_dir = output_dir / f"{input_path.stem}_page_images"
    page_image_dir.mkdir(parents=True, exist_ok=True)

    engine = get_ocr_engine(
        mode=mode.value,
        model_path=model_path,
        server_url=server_url,
        preprocess_mode=preprocess_mode,
    )

    pages: list[OCRResult] = []

    with fitz.open(input_path) as doc:
        total_pages = len(doc)

        for index, page in enumerate(doc, start=1):
            report_progress(
                progress_callback,
                f"Rendering page {index} of {total_pages}...",
            )

            image_path = render_page_to_image(
                page=page,
                output_dir=page_image_dir,
                stem=input_path.stem,
                page_number=index,
                dpi=dpi,
            )

            report_progress(
                progress_callback,
                f"Running OCR on page {index} of {total_pages}...",
            )

            result = engine.ocr_image(
                image_path=image_path,
                page_number=index,
            )

            if result.error:
                report_progress(
                    progress_callback,
                    f"OCR warning on page {index}: {result.error}",
                )

            pages.append(result)

    if not save_page_images:
        report_progress(progress_callback, "Removing temporary page images...")
        shutil.rmtree(page_image_dir, ignore_errors=True)
    else:
        report_progress(
            progress_callback,
            f"Saved rendered page images to: {page_image_dir}",
        )

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
    preprocess_mode: str = "basic",
    progress_callback: Optional[Callable[[str], None]] = None,
) -> OCRDocumentResult:
    engine = get_ocr_engine(
        mode=mode.value,
        model_path=model_path,
        server_url=server_url,
        preprocess_mode=preprocess_mode,
    )

    report_progress(progress_callback, f"Running {mode.value} OCR on image...")

    result = engine.ocr_image(
        image_path=input_path,
        page_number=1,
    )

    if result.error:
        report_progress(progress_callback, f"OCR warning: {result.error}")

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
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    image_path = output_dir / f"{stem}_page_{page_number:04d}.png"
    pix.save(image_path)

    return image_path


def save_ocr_text(result: OCRDocumentResult, output_dir: Path) -> Path:
    output_path = output_dir / f"{result.input_path.stem}_{result.mode.value}.txt"
    output_path.write_text(result.full_text, encoding="utf-8")
    return output_path