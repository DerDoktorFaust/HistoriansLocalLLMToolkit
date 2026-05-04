from datetime import datetime


def format_page_range(start_page, end_page):
    if start_page == end_page:
        return f"p. {start_page}"
    return f"pp. {start_page}–{end_page}"


def write_markdown_output(
    final_summary,
    verification_report,
    batch_summaries,
    chunk_summaries,
    output_path,
    source_file=None,
    model_name=None,
    summary_mode="analytical",
):
    now = datetime.now().isoformat()

    lines = []

    # --- YAML FRONT MATTER ---
    lines.append("---")
    lines.append("title: null")
    lines.append("author: null")
    lines.append("publication_year: null")
    lines.append("publisher_or_journal: null")
    lines.append("work_type: null")

    lines.append(f"source_file: {source_file if source_file else 'null'}")
    lines.append(f"model: {model_name if model_name else 'null'}")
    lines.append(f"summary_mode: {summary_mode}")

    lines.append("model_provider: null")
    lines.append(f"generated_at: {now}")
    lines.append('pipeline_version: "0.1"')
    lines.append("---\n")

    # --- TITLE PLACEHOLDER ---
    if summary_mode == "simple":
        lines.append("# Simple Narrative Summary\n")
    else:
        lines.append("# Document Summary\n")

    # --- TRACEABILITY NOTE ---
    lines.append("## Page Traceability\n")
    lines.append(
        "This summary was generated from page-tracked chunks. "
        "All sections preserve page ranges so claims can be traced back to the original text."
    )
    lines.append("\n---\n")

    # --- FINAL SUMMARY ---
    lines.append("## Final Summary\n")
    lines.append(final_summary.strip())
    lines.append("\n---\n")

    # --- VERIFICATION ---
    lines.append("## Verification Report\n")
    lines.append(verification_report.strip())
    lines.append("\n---\n")

    # --- BATCH SUMMARIES ---
    if batch_summaries:
        lines.append("## Intermediate Batch Summaries\n")

        for i, batch in enumerate(batch_summaries, start=1):
            page_range = format_page_range(batch["start_page"], batch["end_page"])

            lines.append(f"### Batch {i}: {page_range}\n")
            lines.append(f"**Pages covered:** {batch['start_page']}–{batch['end_page']}\n")
            lines.append(batch["summary"].strip())
            lines.append("\n---\n")

    # --- CHUNK SUMMARIES ---
    lines.append("## Chunk Summaries\n")

    for i, item in enumerate(chunk_summaries, start=1):
        chunk = item["chunk"]
        summary = item["summary"]

        page_range = format_page_range(chunk["start_page"], chunk["end_page"])

        lines.append(f"### Chunk {i}: {page_range}\n")
        lines.append(f"**Pages covered:** {chunk['start_page']}–{chunk['end_page']}\n")

        if "pages" in chunk:
            pages = ", ".join(str(p) for p in chunk["pages"])
            lines.append(f"**Individual pages:** {pages}\n")

        lines.append(summary.strip())
        lines.append("\n---\n")

    # --- WRITE FILE ---
    output_path.write_text("\n".join(lines), encoding="utf-8")
