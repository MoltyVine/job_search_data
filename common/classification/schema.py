"""Classification decision schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

RECRUITER_TYPES = (
    "agency_recruiter",
    "inhouse_recruiter",
    "hiring_manager",
    "referral_network",
    "outbound_application",
    "company_rep",
    "ats_system",
    "unknown",
)


@dataclass
class ThreadDecision:
    thread_id: str
    include: bool
    reason: str = ""
    company: str = ""
    position_title: str = ""
    recruiter_type: str = "unknown"
    other_party: str = ""
    source: str = ""  # gmail | linkedin

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ThreadDecision:
        known = {f.name for f in fields(cls)}
        cleaned = {k: v for k, v in data.items() if k in known}
        if "include" in cleaned:
            cleaned["include"] = bool(cleaned["include"])
        return cls(**cleaned)

    @classmethod
    def parse_error_include(cls, thread_id: str, source: str, detail: str = "") -> ThreadDecision:
        """Legacy alias — prefer parse_error_exclude for precision."""
        return cls.parse_error_exclude(thread_id, source, detail)

    @classmethod
    def parse_error_exclude(cls, thread_id: str, source: str, detail: str = "") -> ThreadDecision:
        """Precision-preserving fallback when the model returns unparseable output."""
        return cls(
            thread_id=thread_id,
            include=False,
            reason=f"parse_error{': ' + detail if detail else ''}",
            company="",
            position_title="",
            recruiter_type="unknown",
            other_party="",
            source=source,
        )
