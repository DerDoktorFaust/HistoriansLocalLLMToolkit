from __future__ import annotations

import json
import re
from typing import Any

from src.ner.entity_models import EntityMention
from src.ner.entity_prompts import ENTITY_EXTRACTION_SYSTEM_PROMPT, build_entity_extraction_prompt


def extract_entities_from_chunks(
    chunks: list[dict[str, Any]],
    llm_call,
) -> list[EntityMention]:
    """
    Extract entities from document chunks.

    Expected chunk shape:
    {
        "text": "...",
        "start_page": 1,
        "end_page": 3
    }

    llm_call should be a function that accepts:
        system_prompt: str
        user_prompt: str

    and returns the model response as a string.
    """

    all_entities: list[EntityMention] = []

    for index, chunk in enumerate(chunks, start=1):
        text = chunk.get("text", "")
        page_start = chunk.get("start_page")
        page_end = chunk.get("end_page")

        if not text.strip():
            continue

        print(f"Extracting entities from chunk {index}/{len(chunks)}...")

        prompt = build_entity_extraction_prompt(
            text=text,
            page_start=page_start,
            page_end=page_end,
        )

        raw_response = llm_call(
            system_prompt=ENTITY_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        parsed_entities = parse_entity_response(
            raw_response=raw_response,
            fallback_page_start=page_start,
            fallback_page_end=page_end,
        )

        all_entities.extend(parsed_entities)

    return all_entities


def parse_entity_response(
    raw_response: str,
    fallback_page_start: int | None = None,
    fallback_page_end: int | None = None,
) -> list[EntityMention]:
    data = extract_json_object(raw_response)

    if not data:
        print("Warning: could not parse entity JSON response.")
        return []

    entities = data.get("entities", [])

    if not isinstance(entities, list):
        print("Warning: entity JSON did not contain an entities list.")
        return []

    results: list[EntityMention] = []

    for item in entities:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        entity_type = item.get("entity_type")

        if not name or not entity_type:
            continue

        mention = EntityMention(
            name=name,
            entity_type=entity_type,
            normalized_name=item.get("normalized_name") or name,
            page_start=item.get("page_start") or fallback_page_start,
            page_end=item.get("page_end") or fallback_page_end,
            evidence=item.get("evidence"),
            confidence=item.get("confidence"),
            notes=item.get("notes"),
        ).clean()

        results.append(mention)

    return results


def extract_json_object(raw_response: str) -> dict[str, Any] | None:
    """
    Handles:
    - pure JSON
    - JSON inside ```json fences
    - extra model text before/after JSON
    """

    if not raw_response:
        return None

    text = raw_response.strip()

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        text = fenced_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    first = text.find("{")
    last = text.rfind("}")

    if first == -1 or last == -1 or last <= first:
        return None

    candidate = text[first : last + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None