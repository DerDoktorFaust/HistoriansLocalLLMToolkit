# src/translation/translation_core.py

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import fitz  # PyMuPDF
import requests

from src.ocr.ocr_core import run_ocr


DEFAULT_CHUNK_CHAR_LIMIT = 6000


def report_progress(
    progress_callback: Optional[Callable[[str], None]],
    message: str,
) -> None:
    if progress_callback:
        progress_callback(message)


def normalize_lm_studio_base_url(model_path: str) -> str:
    if not model_path:
        raise ValueError("No LM Studio server URL provided.")

    server_url = model_path.rstrip("/")
    if server_url.endswith("/v1"):
        return server_url
    return f"{server_url}/v1"


def get_loaded_model_id(api_base_url: str) -> str:
    models_url = f"{api_base_url}/models"
    response = requests.get(models_url, timeout=30)
    response.raise_for_status()

    data = response.json()
    models = data.get("data", [])

    if not models:
        raise ValueError("LM Studio returned no loaded models.")

    return models[0]["id"]


def is_usable_text(text: str, min_chars: int = 200) -> bool:
    cleaned = (text or "").strip()
    if len(cleaned) < min_chars:
        return False

    # Avoid treating page markers or extraction noise as meaningful text.
    alphanumeric_chars = sum(char.isalnum() for char in cleaned)
    return alphanumeric_chars >= min_chars * 0.5


def existing_text_candidates(pdf_path: Path) -> list[Path]:
    return [
        pdf_path.parent / f"{pdf_path.stem}_ocr.txt",
        pdf_path.parent / f"{pdf_path.stem}_extracted_text.txt",
        pdf_path.parent / f"{pdf_path.stem}.txt",
    ]


def load_existing_text_if_available(
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str | None:
    for candidate in existing_text_candidates(pdf_path):
        if candidate.exists():
            report_progress(progress_callback, f"Found existing text file: {candidate.name}")
            text = candidate.read_text(encoding="utf-8", errors="replace")
            if is_usable_text(text):
                report_progress(progress_callback, "Using existing extracted/OCR text.")
                return text

            report_progress(
                progress_callback,
                f"Ignoring {candidate.name} because it does not contain enough usable text.",
            )

    return None


def extract_embedded_pdf_text(
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    pages: list[str] = []

    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)
        for index, page in enumerate(doc, start=1):
            report_progress(
                progress_callback,
                f"Checking embedded PDF text on page {index} of {total_pages}...",
            )
            text = page.get_text("text") or ""
            pages.append(f"\n\n--- Page {index} ---\n\n{text.strip()}")

    return "\n".join(pages).strip()


def save_extracted_text(pdf_path: Path, text: str) -> Path:
    output_path = pdf_path.parent / f"{pdf_path.stem}_extracted_text.txt"
    output_path.write_text(text, encoding="utf-8")
    return output_path


def get_text_for_translation(
    pdf_path: Path,
    model_path: str,
    ocr_mode: str = "extract_text",
    preprocess_mode: str = "basic",
    save_page_images: bool = False,
    tesseract_language: str = "eng",
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    existing_text = load_existing_text_if_available(pdf_path, progress_callback)
    if existing_text:
        return existing_text

    report_progress(progress_callback, "No usable existing text file found.")
    report_progress(progress_callback, "Trying embedded PDF text extraction...")

    extracted_text = extract_embedded_pdf_text(pdf_path, progress_callback)
    if is_usable_text(extracted_text):
        output_path = save_extracted_text(pdf_path, extracted_text)
        report_progress(progress_callback, f"Saved extracted text to: {output_path}")
        return extracted_text

    report_progress(progress_callback, "Embedded PDF text was not usable.")

    if ocr_mode == "extract_text":
        raise ValueError(
            "Translation requires usable text, but this PDF does not appear to contain "
            "extractable text. Choose an OCR method such as Tesseract, LLM Vision, or "
            "Tesseract + LLM Vision, then run translation again."
        )

    report_progress(progress_callback, "Running OCR so the text can be translated...")
    ocr_result = run_ocr(
        input_path=pdf_path,
        output_dir=pdf_path.parent,
        mode=ocr_mode,
        model_path=model_path,
        preprocess_mode=preprocess_mode,
        save_txt=True,
        save_page_images=save_page_images,
        tesseract_language=tesseract_language,
        progress_callback=progress_callback,
    )

    if not is_usable_text(ocr_result.full_text):
        raise ValueError("OCR completed, but it did not produce enough usable text to translate.")

    return ocr_result.full_text


def split_text_into_chunks(text: str, max_chars: int = DEFAULT_CHUNK_CHAR_LIMIT) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        paragraph_length = len(paragraph)

        if paragraph_length > max_chars:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_length = 0

            for start in range(0, paragraph_length, max_chars):
                chunks.append(paragraph[start : start + max_chars])
            continue

        if current and current_length + paragraph_length + 2 > max_chars:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_length = paragraph_length
        else:
            current.append(paragraph)
            current_length += paragraph_length + 2

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def translate_chunk_with_lm_studio(
    chunk: str,
    model_path: str,
    target_language: str,
    chunk_number: int,
    total_chunks: int,
) -> str:
    api_base_url = normalize_lm_studio_base_url(model_path)
    api_url = f"{api_base_url}/chat/completions"
    model_id = get_loaded_model_id(api_base_url)

    system_prompt = (
        "You are a careful scholarly translator for historians. "
        "Translate the user's text into the requested target language. "
        "Auto-detect the source language. Preserve names, dates, archival references, "
        "page markers, headings, paragraph breaks, and formatting where possible. "
        "Do not summarize, explain, modernize, omit, or add commentary. "
        "If a word or phrase is illegible or uncertain, preserve it and mark it as [unclear]."
    )

    user_prompt = (
        f"Translate the following text into {target_language}.\n\n"
        f"This is chunk {chunk_number} of {total_chunks}. "
        "Return only the translation.\n\n"
        f"{chunk}"
    )

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "max_tokens": 4096,
    }

    response = requests.post(api_url, json=payload, timeout=300)

    if response.status_code >= 400:
        raise RuntimeError(f"{response.status_code} error from LM Studio: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def translate_text_with_lm_studio(
    text: str,
    model_path: str,
    target_language: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    chunks = split_text_into_chunks(text)
    if not chunks:
        raise ValueError("No text was available to translate.")

    translations: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        report_progress(progress_callback, f"Translating chunk {index} of {len(chunks)}...")
        translations.append(
            translate_chunk_with_lm_studio(
                chunk=chunk,
                model_path=model_path,
                target_language=target_language,
                chunk_number=index,
                total_chunks=len(chunks),
            )
        )

    return "\n\n".join(translations).strip()


def translate_pdf(
    pdf_path: str | Path,
    model_path: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    target_language: str = "English",
    ocr_mode: str = "extract_text",
    preprocess_mode: str = "basic",
    save_page_images: bool = False,
    tesseract_language: str = "eng",
) -> str:
    pdf_path = Path(pdf_path)

    report_progress(progress_callback, "Preparing translation job...")
    report_progress(progress_callback, "Source language: Auto-detect")
    report_progress(progress_callback, f"Target language: {target_language}")

    text = get_text_for_translation(
        pdf_path=pdf_path,
        model_path=model_path,
        ocr_mode=ocr_mode,
        preprocess_mode=preprocess_mode,
        save_page_images=save_page_images,
        tesseract_language=tesseract_language,
        progress_callback=progress_callback,
    )

    translated_text = translate_text_with_lm_studio(
        text=text,
        model_path=model_path,
        target_language=target_language,
        progress_callback=progress_callback,
    )

    return (
        f"# Translation\n\n"
        f"Source file: `{pdf_path.name}`\n\n"
        f"Source language: Auto-detect\n\n"
        f"Target language: {target_language}\n\n"
        f"---\n\n"
        f"{translated_text}\n"
    )
