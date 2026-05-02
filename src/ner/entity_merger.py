from __future__ import annotations

import re
from collections import defaultdict

from src.ner.entity_models import EntityMention, MergedEntity


def merge_entities(mentions: list[EntityMention]) -> list[MergedEntity]:
    grouped: dict[tuple[str, str], MergedEntity] = {}

    for mention in mentions:
        key = make_entity_key(mention)

        if key not in grouped:
            grouped[key] = MergedEntity(
                normalized_name=mention.normalized_name or mention.name,
                entity_type=mention.entity_type,
            )

        grouped[key].add_mention(mention)

    merged = list(grouped.values())

    merged.sort(
        key=lambda entity: (
            entity.entity_type,
            entity.normalized_name.lower(),
        )
    )

    return merged


def make_entity_key(mention: EntityMention) -> tuple[str, str]:
    name = mention.normalized_name or mention.name
    return normalize_key(name), mention.entity_type.upper()


def normalize_key(name: str) -> str:
    value = name.lower().strip()

    value = re.sub(r"^[Tt]he\s+", "", value)
    value = re.sub(r"[^\w\s\-]", "", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def get_entity_counts(mentions: list[EntityMention]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)

    for mention in mentions:
        counts[mention.entity_type] += 1

    return dict(sorted(counts.items()))