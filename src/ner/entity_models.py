from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class EntityMention:
    name: str
    entity_type: str
    normalized_name: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    evidence: str | None = None
    confidence: str | None = None
    notes: str | None = None

    def clean(self) -> "EntityMention":
        self.name = clean_text(self.name)
        self.entity_type = clean_text(self.entity_type).upper()
        self.normalized_name = clean_text(self.normalized_name) if self.normalized_name else self.name
        self.evidence = clean_text(self.evidence) if self.evidence else None
        self.confidence = clean_text(self.confidence).lower() if self.confidence else None
        self.notes = clean_text(self.notes) if self.notes else None
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MergedEntity:
    normalized_name: str
    entity_type: str
    names_seen: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
    mentions: list[EntityMention] = field(default_factory=list)

    def add_mention(self, mention: EntityMention) -> None:
        if mention.name and mention.name not in self.names_seen:
            self.names_seen.append(mention.name)

        if mention.page_start is not None:
            self.pages.append(mention.page_start)

        if mention.page_end is not None and mention.page_end != mention.page_start:
            self.pages.append(mention.page_end)

        self.pages = sorted(set(self.pages))
        self.mentions.append(mention)

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalized_name": self.normalized_name,
            "entity_type": self.entity_type,
            "names_seen": self.names_seen,
            "pages": self.pages,
            "mention_count": len(self.mentions),
            "mentions": [m.to_dict() for m in self.mentions],
        }


def clean_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())