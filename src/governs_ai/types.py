from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PrecheckResult:
    decision: str
    redacted_content: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
