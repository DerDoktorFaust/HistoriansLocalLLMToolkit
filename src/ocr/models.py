from dataclasses import dataclass
from typing import Optional


@dataclass
class OCRResult:
    text: str
    engine: str
    page_number: Optional[int] = None
    confidence: Optional[float] = None
    error: Optional[str] = None