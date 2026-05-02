import argparse
import logging
import time
from pathlib import Path

from .extractor import extract_pages
from .chunker import chunk_pages
from .classifier import classify_document
from .llm import load_model, unload_model, MODEL_PATH
from .summarizer import (
    summarize_article,
    summarize_book,
    build_final_summary
)
from .writer import write_markdown_output


def setup_logging():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_path = logs_dir / f"run_{int(time.time())}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

    return log_path


def run_summarizer(pdf_path, output_dir=None, progress_callback=None):
    log_path = setup_logging()

    start_time = time.time()
    errors = 0
    model_loaded = False

    pdf_path = Path(pdf_path)

    if output_dir is None:
        output_dir = Path("output")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)

    def progress(message):
        logging.info(message)
        if progress_callback:
            progress_callback(message)

    try:
        progress(f"Starting summarization for: {pdf_path}")

        # --- Extract text ---
        progress("Extracting PDF text...")
        pages = extract_pages(pdf_path)
        total_pages = len(pages)
        progress(f"Extracted {total_pages} pages.")

        # --- Classify document ---
        progress("Classifying document type...")
        document_type = classify_document(pages)
        progress(f"Detected document type: {document_type}")

        # --- Chunking ---
        progress("Chunking document...")
        chunks = chunk_pages(pages, document_type=document_type)
        total_chunks = len(chunks)
        progress(f"Created {total_chunks} chunks.")

        # --- Load model ---
        progress("Loading model...")
        model = load_model(MODEL_PATH)
        model_loaded = True

        chunk_summaries = []

        # --- Process chunks ---
        progress("Processing chunks...")
        for i, chunk in enumerate(chunks, start=1):
            progress(f"Processing chunk {i}/{total_chunks}...")

            try:
                if document_type == "article":
                    summary = summarize_article(model, chunk)
                else:
                    summary = summarize_book(model, chunk)

                chunk_summaries.append(summary)

            except Exception as e:
                errors += 1
                logging.error(f"Error on chunk {i}: {e}")
                chunk_summaries.append(f"[ERROR: Chunk {i} failed]")

        # --- Final summary ---
        progress("Building final summary...")
        final_summary = build_final_summary(model, chunk_summaries)

        # --- Write output ---
        progress("Writing output...")
        output_path = write_markdown_output(
            output_dir=output_dir,
            input_filename=pdf_path.stem,
            final_summary=final_summary,
            chunk_summaries=chunk_summaries
        )

        total_time = time.time() - start_time

        progress("Summarization complete.")
        progress(f"Output saved to: {output_path}")
        progress(f"Total time: {total_time:.2f} seconds")
        progress(f"Errors: {errors}")

        return {
            "output_path": str(output_path),
            "log_path": str(log_path),
            "document_type": document_type,
            "pages": total_pages,
            "chunks": total_chunks,
            "errors": errors,
            "total_time": total_time,
        }

    finally:
        if model_loaded:
            progress("Unloading model...")
            unload_model()


# --- CLI support (optional) ---

def parse_args():
    parser = argparse.ArgumentParser(description="Summarize a PDF document.")
    parser.add_argument("pdf", help="Path to PDF file")
    return parser.parse_args()


def main():
    args = parse_args()
    result = run_summarizer(args.pdf)
    print(f"\nSummary saved to: {result['output_path']}")


if __name__ == "__main__":
    main()