from __future__ import annotations

import csv
import json
from pathlib import Path

from src.ner.entity_models import EntityMention, MergedEntity


def write_entity_outputs(
    mentions: list[EntityMention],
    merged_entities: list[MergedEntity],
    output_dir: Path,
    base_filename: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    write_mentions_json(
        mentions=mentions,
        output_path=output_dir / f"{base_filename}_entity_mentions.json",
    )

    write_merged_json(
        merged_entities=merged_entities,
        output_path=output_dir / f"{base_filename}_entities.json",
    )

    write_entities_csv(
        merged_entities=merged_entities,
        output_path=output_dir / f"{base_filename}_entities.csv",
    )

    write_entities_markdown(
        merged_entities=merged_entities,
        output_path=output_dir / f"{base_filename}_entities.md",
        title=base_filename,
    )


def write_mentions_json(
    mentions: list[EntityMention],
    output_path: Path,
) -> None:
    data = [mention.to_dict() for mention in mentions]

    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_merged_json(
    merged_entities: list[MergedEntity],
    output_path: Path,
) -> None:
    data = [entity.to_dict() for entity in merged_entities]

    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_entities_csv(
    merged_entities: list[MergedEntity],
    output_path: Path,
) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_name",
                "entity_type",
                "names_seen",
                "pages",
                "mention_count",
            ],
        )

        writer.writeheader()

        for entity in merged_entities:
            writer.writerow(
                {
                    "normalized_name": entity.normalized_name,
                    "entity_type": entity.entity_type,
                    "names_seen": "; ".join(entity.names_seen),
                    "pages": ", ".join(str(page) for page in entity.pages),
                    "mention_count": len(entity.mentions),
                }
            )


def write_entities_markdown(
    merged_entities: list[MergedEntity],
    output_path: Path,
    title: str,
) -> None:
    lines: list[str] = []

    lines.append(f"# Named Entities: {title}")
    lines.append("")

    grouped: dict[str, list[MergedEntity]] = {}

    for entity in merged_entities:
        grouped.setdefault(entity.entity_type, []).append(entity)

    for entity_type in sorted(grouped.keys()):
        lines.append(f"## {entity_type}")
        lines.append("")

        for entity in grouped[entity_type]:
            pages = ", ".join(str(page) for page in entity.pages) if entity.pages else "unknown"
            names_seen = "; ".join(entity.names_seen)

            lines.append(f"### {entity.normalized_name}")
            lines.append("")
            lines.append(f"- **Mentions:** {len(entity.mentions)}")
            lines.append(f"- **Pages:** {pages}")
            lines.append(f"- **Names seen:** {names_seen}")

            first_evidence = next(
                (mention.evidence for mention in entity.mentions if mention.evidence),
                None,
            )

            if first_evidence:
                lines.append(f"- **Sample evidence:** {first_evidence}")

            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")