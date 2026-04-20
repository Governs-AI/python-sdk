from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PrecheckResult:
    decision: str
    redacted_content: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    latency_ms: float = 0.0


@dataclass
class BudgetResult:
    """Result of a budget_check call.

    Example::

        budget = client.budget_check(
            org_id="org-1",
            user_id="user-1",
            estimated_tokens=500,
        )
        if not budget.allowed:
            raise RuntimeError("Budget exceeded")
        if budget.warning_threshold_hit:
            logger.warning("Less than 10% budget remaining")
    """

    allowed: bool
    remaining_tokens: int
    limit: int
    warning_threshold_hit: bool
    reason: str = ""
