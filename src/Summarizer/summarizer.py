from src.summarizer.llm import generate_text

from src.summarizer.prompts import (
    batch_synthesis_prompt,
    chunk_summary_prompt,
    final_summary_prompt,
    verification_prompt,
    article_final_summary_prompt,
    article_verification_prompt
)


def summarize_chunk(chunk):
    prompt = chunk_summary_prompt(chunk)
    return generate_text(prompt)


def extract_compressed_notes(summary):
    marker = "## Compressed Notes"

    if marker in summary:
        return summary.split(marker, 1)[1].strip()

    return summary[:1200].strip()


def synthesize_batches(chunk_summaries, batch_size=6):
    batch_summaries = []

    for i in range(0, len(chunk_summaries), batch_size):
        batch = chunk_summaries[i:i + batch_size]

        combined = "\n\n".join(
            f"Pages {s['chunk']['start_page']}–{s['chunk']['end_page']}:\n"
            f"{s['compressed_notes']}"
            for s in batch
        )

        prompt = batch_synthesis_prompt(combined)
        batch_summary = generate_text(prompt)

        batch_summaries.append({
            "start_page": batch[0]["chunk"]["start_page"],
            "end_page": batch[-1]["chunk"]["end_page"],
            "summary": batch_summary,
        })

    return batch_summaries


def synthesize_final_summary(batch_summaries):
    combined = "\n\n".join(
        f"Pages {b['start_page']}–{b['end_page']}:\n{b['summary']}"
        for b in batch_summaries
    )

    prompt = final_summary_prompt(combined)
    return generate_text(prompt)


def verify_final_summary(final_summary, batch_summaries):
    combined = "\n\n".join(
        f"Pages {b['start_page']}–{b['end_page']}:\n{b['summary']}"
        for b in batch_summaries
    )

    prompt = verification_prompt(final_summary, combined)
    return generate_text(prompt)

def synthesize_article_summary(chunk_summaries):
    combined = "\n\n".join(
        f"Pages {s['chunk']['start_page']}–{s['chunk']['end_page']}:\n"
        f"{s['compressed_notes']}"
        for s in chunk_summaries
    )

    prompt = article_final_summary_prompt(combined)
    return generate_text(prompt)


def verify_article_summary(final_summary, chunk_summaries):
    combined = "\n\n".join(
        f"Pages {s['chunk']['start_page']}–{s['chunk']['end_page']}:\n"
        f"{s['compressed_notes']}"
        for s in chunk_summaries
    )

    prompt = article_verification_prompt(final_summary, combined)
    return generate_text(prompt)