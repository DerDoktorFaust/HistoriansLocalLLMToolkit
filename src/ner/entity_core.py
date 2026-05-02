from pathlib import Path

from src.summarizer.extractor import extract_pages
from src.summarizer.chunker import chunk_pages
from src.llm.llm import load_model, unload_model, generate_text
from src.ner.entity_extractor import extract_entities_from_chunks
from src.ner.entity_merger import merge_entities


def named_entity_recognition_pdf(
    pdf_path: Path,
    model_path: str,
    progress_callback,
) -> str:
    progress_callback("Starting named entity recognition...")
    progress_callback(f"PDF: {pdf_path.name}")

    progress_callback("Extracting text from PDF...")
    text = extract_pages(pdf_path)

    progress_callback("Chunking text...")
    chunks = chunk_pages(text)

    progress_callback(f"Created {len(chunks)} chunks for entity extraction.")

    progress_callback("Loading model...")
    load_model(model_path)

    try:
        def llm_call(system_prompt: str, user_prompt: str) -> str:
            return generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.0,
            )

        progress_callback("Extracting entities...")
        mentions = extract_entities_from_chunks(
            chunks=chunks,
            llm_call=llm_call,
        )

        progress_callback(f"Found {len(mentions)} entity mentions.")

        progress_callback("Merging duplicate entities...")
        merged_entities = merge_entities(mentions)

        progress_callback(f"Merged into {len(merged_entities)} unique entities.")

    finally:
        progress_callback("Unloading model...")
        unload_model()

    progress_callback("Building entity report...")
    return build_entities_markdown(pdf_path, merged_entities)


def build_entities_markdown(pdf_path: Path, merged_entities) -> str:
    lines: list[str] = []

    lines.append(f"# Named Entities: {pdf_path.name}")
    lines.append("")

    if not merged_entities:
        lines.append("No named entities were extracted.")
        return "\n".join(lines)

    grouped: dict[str, list] = {}

    for entity in merged_entities:
        grouped.setdefault(entity.entity_type, []).append(entity)

    for entity_type in sorted(grouped.keys()):
        lines.append(f"## {entity_type}")
        lines.append("")

        entities = sorted(
            grouped[entity_type],
            key=lambda entity: entity.normalized_name.lower(),
        )

        for entity in entities:
            pages = (
                ", ".join(str(page) for page in entity.pages)
                if entity.pages
                else "unknown"
            )

            names_seen = (
                "; ".join(entity.names_seen)
                if entity.names_seen
                else entity.normalized_name
            )

            lines.append(f"### {entity.normalized_name}")
            lines.append("")
            lines.append(f"- **Mentions:** {len(entity.mentions)}")
            lines.append(f"- **Pages:** {pages}")
            lines.append(f"- **Names seen:** {names_seen}")

            sample_evidence = get_sample_evidence(entity)

            if sample_evidence:
                lines.append(f"- **Sample evidence:** {sample_evidence}")

            lines.append("")

    return "\n".join(lines)


def get_sample_evidence(entity) -> str | None:
    for mention in entity.mentions:
        if mention.evidence:
            return mention.evidence
    return None