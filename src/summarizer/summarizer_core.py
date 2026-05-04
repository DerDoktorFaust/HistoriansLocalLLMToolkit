import logging
import time
from pathlib import Path

from src.summarizer.extractor import extract_pages
from src.summarizer.chunker import chunk_pages
from src.summarizer.classifier import classify_document
from src.llm.llm import load_model, unload_model
from src.summarizer.summarizer import (
    summarize_chunk,
    extract_compressed_notes,
    synthesize_batches,
    synthesize_final_summary,
    verify_final_summary,
    synthesize_article_summary,
    verify_article_summary,
    summarize_simple_chunk,
    extract_simple_narrative_notes,
    synthesize_simple_summary,
    verify_simple_summary,
)
from src.summarizer.writer import write_markdown_output


VALID_SUMMARY_MODES = {"analytical", "simple"}


def analytical_summarize_pdf(pdf_path: Path, model_path: str, progress_callback):
    return run_summarizer(
        pdf_path=pdf_path,
        model_path=model_path,
        progress_callback=progress_callback,
        summary_mode="analytical",
    )


def simple_summarize_pdf(pdf_path: Path, model_path: str, progress_callback):
    return run_summarizer(
        pdf_path=pdf_path,
        model_path=model_path,
        progress_callback=progress_callback,
        summary_mode="simple",
    )


def setup_logging():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_path = logs_dir / f"run_{int(time.time())}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
        force=True,
    )

    return log_path


def build_markdown(
    final_summary,
    verification_report,
    batch_summaries,
    chunk_summaries,
    source_file,
    model_name=None,
    summary_mode="analytical",
):
    temp_output_path = Path("__temp_summary_output.md")

    write_markdown_output(
        final_summary=final_summary,
        verification_report=verification_report,
        batch_summaries=batch_summaries,
        chunk_summaries=chunk_summaries,
        output_path=temp_output_path,
        source_file=source_file,
        model_name=model_name,
        summary_mode=summary_mode,
    )

    markdown = temp_output_path.read_text(encoding="utf-8")
    temp_output_path.unlink(missing_ok=True)

    return markdown


def run_summarizer(pdf_path, model_path=None, progress_callback=None, summary_mode="analytical"):
    """
    Main callable summarizer function for both CLI and GUI.

    Takes:
        pdf_path: path to PDF
        model_path: optional model path override
        progress_callback: optional function for GUI progress updates
        summary_mode: "analytical" or "simple"

    Returns:
        markdown string
    """

    setup_logging()

    if summary_mode not in VALID_SUMMARY_MODES:
        raise ValueError(
            f"Invalid summary_mode: {summary_mode}. "
            f"Expected one of: {', '.join(sorted(VALID_SUMMARY_MODES))}"
        )

    start_time = time.time()
    errors = 0
    model_loaded = False

    pdf_path = Path(pdf_path)

    def progress(message):
        logging.info(message)
        if progress_callback:
            progress_callback(message)

    try:
        progress(f"Starting {summary_mode} summarization for: {pdf_path}")

        progress("Extracting PDF text...")
        pages = extract_pages(pdf_path)
        total_pages = len(pages)
        progress(f"Extracted {total_pages} pages.")

        progress("Classifying document type...")
        document_type = classify_document(total_pages)
        progress(f"Detected document type: {document_type}")

        progress("Chunking document...")
        chunks = chunk_pages(pages)
        total_chunks = len(chunks)
        progress(f"Created {total_chunks} chunks.")

        progress("Loading model...")
        load_model(model_path=model_path)
        model_loaded = True

        chunk_summaries = []

        progress("Processing chunks...")
        for i, chunk in enumerate(chunks, start=1):
            progress(f"Processing chunk {i}/{total_chunks}: pages {chunk['start_page']}–{chunk['end_page']}")

            try:
                if summary_mode == "simple":
                    summary = summarize_simple_chunk(chunk)
                    compressed_notes = extract_simple_narrative_notes(summary)
                else:
                    summary = summarize_chunk(chunk)
                    compressed_notes = extract_compressed_notes(summary)

                chunk_summaries.append({
                    "chunk": chunk,
                    "summary": summary,
                    "compressed_notes": compressed_notes,
                })

            except Exception as e:
                errors += 1
                logging.exception(f"Error on chunk {i}")

                chunk_summaries.append({
                    "chunk": chunk,
                    "summary": f"[ERROR: Chunk {i} failed: {e}]",
                    "compressed_notes": f"[ERROR: Chunk {i} failed: {e}]",
                })

        if summary_mode == "simple":
            progress("Synthesizing simple narrative summary...")
            final_summary = synthesize_simple_summary(chunk_summaries)

            progress("Verifying simple narrative summary...")
            verification_report = verify_simple_summary(final_summary, chunk_summaries)

            batch_summaries = []

        elif document_type == "article":
            progress("Synthesizing final article summary...")
            final_summary = synthesize_article_summary(chunk_summaries)

            progress("Verifying article summary...")
            verification_report = verify_article_summary(final_summary, chunk_summaries)

            batch_summaries = []

        else:
            progress("Synthesizing intermediate batch summaries...")
            batch_summaries = synthesize_batches(chunk_summaries)

            progress("Synthesizing final book summary...")
            final_summary = synthesize_final_summary(batch_summaries)

            progress("Verifying final book summary...")
            verification_report = verify_final_summary(final_summary, batch_summaries)

        progress("Building Markdown output...")

        markdown = build_markdown(
            final_summary=final_summary,
            verification_report=verification_report,
            batch_summaries=batch_summaries,
            chunk_summaries=chunk_summaries,
            source_file=str(pdf_path),
            model_name=model_path,
            summary_mode=summary_mode,
        )

        total_time = time.time() - start_time

        progress("Summarization complete.")
        progress(f"Total time: {total_time:.2f} seconds")
        progress(f"Errors: {errors}")

        return markdown

    finally:
        if model_loaded:
            progress("Unloading model...")
            unload_model()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Summarize a PDF document.")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--output", "-o", help="Output Markdown file")
    parser.add_argument("--model-path", help="Optional model path override")
    parser.add_argument(
        "--mode",
        choices=sorted(VALID_SUMMARY_MODES),
        default="analytical",
        help="Summary mode: analytical or simple",
    )

    args = parser.parse_args()

    markdown = run_summarizer(
        pdf_path=args.pdf,
        model_path=args.model_path,
        summary_mode=args.mode,
    )

    if args.output:
        output_path = Path(args.output)
    else:
        suffix = ".simple-summary.md" if args.mode == "simple" else ".summary.md"
        output_path = Path(args.pdf).with_suffix(suffix)

    output_path.write_text(markdown, encoding="utf-8")
    print(f"Summary saved to: {output_path}")


if __name__ == "__main__":
    main()
