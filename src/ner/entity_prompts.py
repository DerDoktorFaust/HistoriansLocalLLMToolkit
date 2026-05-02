ENTITY_TYPES = [
    "PERSON",
    "ORG",
    "GPE",
    "LOC",
    "DATE",
    "EVENT",
    "WORK",
    "LAW_TREATY",
    "MONEY",
    "CONCEPT",
    "OTHER",
]


ENTITY_EXTRACTION_SYSTEM_PROMPT = """
You extract named entities from historical and scholarly text.

Rules:
- Extract only entities explicitly present in the text.
- Do not infer entities that are not named.
- Do not summarize the passage.
- Do not explain your reasoning.
- Do not invent dates, people, places, institutions, or titles.
- Preserve historically specific names when possible.
- Use normalized_name to merge obvious variants, but do not over-normalize uncertain cases.
- Evidence must be a short exact phrase or sentence fragment from the text.
- Return valid JSON only.

Entity types:
PERSON: individual people.
ORG: organizations, institutions, agencies, commissions, companies, parties.
GPE: states, countries, cities, empires, political-geographic units.
LOC: geographic places that are not political units, such as regions, rivers, mountains.
DATE: dates, years, periods, named eras.
EVENT: named historical events, wars, revolutions, crises, conferences.
WORK: books, articles, newspapers, speeches, reports, publications.
LAW_TREATY: laws, treaties, agreements, legal instruments.
MONEY: currencies, sums, indemnities, debts, loans, financial amounts.
CONCEPT: named ideas, doctrines, theories, ideologies, analytical concepts.
OTHER: named entities that do not fit the above.
""".strip()


def build_entity_extraction_prompt(
    text: str,
    page_start: int | None = None,
    page_end: int | None = None,
) -> str:
    page_info = ""

    if page_start is not None and page_end is not None:
        page_info = f"Pages: {page_start}–{page_end}"
    elif page_start is not None:
        page_info = f"Page: {page_start}"

    return f"""
Extract named entities from the following text.

{page_info}

Return JSON in exactly this structure:

{{
  "entities": [
    {{
      "name": "entity exactly as it appears",
      "entity_type": "PERSON | ORG | GPE | LOC | DATE | EVENT | WORK | LAW_TREATY | MONEY | CONCEPT | OTHER",
      "normalized_name": "standardized form, if obvious; otherwise same as name",
      "page_start": {page_start if page_start is not None else "null"},
      "page_end": {page_end if page_end is not None else "null"},
      "evidence": "short quotation proving the entity appears in the text",
      "confidence": "high | medium | low",
      "notes": "brief note only if needed; otherwise null"
    }}
  ]
}}

Text:
\"\"\"
{text}
\"\"\"
""".strip()