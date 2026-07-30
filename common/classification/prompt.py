"""Prompt builders for thread classification (used by the openrouter backend)."""

from __future__ import annotations

import json
import re
from typing import Any

from .criteria import load_criteria
from .schema import RECRUITER_TYPES, ThreadDecision

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")

# Types allowed for include=true (ats_system kept in schema for old decisions only)
_INCLUDE_TYPES = (
    "agency_recruiter",
    "inhouse_recruiter",
    "hiring_manager",
    "referral_network",
    "outbound_application",
    "company_rep",
)


def system_prompt(criteria_text: str | None = None) -> str:
    criteria = criteria_text if criteria_text is not None else load_criteria()
    types = ", ".join(_INCLUDE_TYPES)
    return (
        "You classify job-search conversations for archival.\n"
        "INCLUDE only if a real person discusses one or more job opportunities "
        "with the participant (multi-role threads still count).\n"
        "EXCLUDE automated mail (job alerts, Otta matches, noreply application receipts, "
        "Slack unread digests, DocuSign/contracts, bank appointments, careers marketing).\n"
        "When unsure, set include=false (prefer precision).\n\n"
        f"Criteria:\n{criteria}\n\n"
        "Respond with ONLY a single JSON object (no markdown fences) with keys:\n"
        "  include (boolean),\n"
        "  reason (short string),\n"
        "  company (string; empty if exclude),\n"
        '  position_title (string; use "Unspecified" if include but unknown; '
        "if several roles, semicolon-separated main titles),\n"
        f"  recruiter_type (one of: {types} when include=true; "
        "unknown ONLY when include=false),\n"
        "  other_party (human counterpart name; empty if unknown).\n"
        "If include=true you MUST set recruiter_type to one of the listed types "
        "(never unknown).\n"
    )


def user_prompt(thread_text: str, *, thread_id: str, source: str) -> str:
    return (
        f"Source: {source}\n"
        f"Thread ID: {thread_id}\n\n"
        "Decide include=true only for real-person recruiting about one or more job "
        "opportunities (not automated digests / marketing).\n\n"
        f"Thread:\n{thread_text}\n"
    )


def parse_model_json(raw: str, *, thread_id: str, source: str) -> ThreadDecision:
    text = (raw or "").strip()
    if not text:
        return ThreadDecision.parse_error_exclude(thread_id, source, "empty response")

    candidate = text
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        candidate = fence.group(1).strip()
    else:
        match = _JSON_BLOCK.search(text)
        if match:
            candidate = match.group(0)

    try:
        data: dict[str, Any] = json.loads(candidate)
    except json.JSONDecodeError:
        return ThreadDecision.parse_error_exclude(thread_id, source, "invalid json")

    include = data.get("include")
    if include is None:
        for alt in ("Include", "keep", "Keep", "relevant", "is_include"):
            if alt in data:
                include = data[alt]
                break
    if isinstance(include, str):
        include = include.strip().lower() in {"1", "true", "yes", "y"}
    elif include is None:
        # Model sometimes omits include but fills recruiting fields
        rtype_guess = str(data.get("recruiter_type") or "").strip()
        if rtype_guess in _INCLUDE_TYPES and (
            data.get("company") or data.get("position_title") or data.get("other_party")
        ):
            include = True
        else:
            return ThreadDecision.parse_error_exclude(thread_id, source, "missing include")

    rtype = str(data.get("recruiter_type") or "unknown").strip()
    if rtype == "ats_system":
        # Deprecated for includes — treat as exclude unless model also marked include
        # with a human type; force unknown and prefer exclude path via criteria.
        rtype = "unknown"
    if rtype not in RECRUITER_TYPES:
        rtype = "unknown"

    include_bool = bool(include)
    reason = str(data.get("reason") or "").strip()
    position_title = str(data.get("position_title") or "").strip()
    other_party = str(data.get("other_party") or "").strip()
    company = str(data.get("company") or "").strip()
    # Models sometimes copy the docs placeholder literally
    if "AgencyName" in company:
        company = f"Undisclosed (via {other_party or 'agency'})"
    party_l = other_party.lower()
    junk_party = any(
        x in party_l
        for x in (
            "mail delivery",
            "noreply",
            "no-reply",
            "no reply",
            "donotreply",
            "do-not-reply",
        )
    )

    # Models often set include=true but leave recruiter_type=unknown.
    # Default the taxonomy rather than flipping away a real include — except
    # when the counterpart looks automated / bounce mail.
    if include_bool and junk_party:
        include_bool = False
        rtype = "unknown"
        reason = (reason + "; " if reason else "") + "excluded_junk_party"
    elif include_bool and rtype not in _INCLUDE_TYPES:
        rtype = "company_rep"
        reason = (reason + "; " if reason else "") + "defaulted_type_company_rep"

    return ThreadDecision(
        thread_id=thread_id,
        include=include_bool,
        reason=reason,
        company=company,
        position_title=position_title or ("Unspecified" if include_bool else ""),
        recruiter_type=rtype if include_bool else (rtype or "unknown"),
        other_party=other_party,
        source=source,
    )
