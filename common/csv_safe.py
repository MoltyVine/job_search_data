"""Helpers for safer CSV exports from untrusted message content."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping


def csv_safe_cell(value: Any) -> Any:
    """Neutralize spreadsheet formula injection for string cells.

    Excel/LibreOffice treat leading ``=``, ``+``, ``-``, ``@`` (and some
    whitespace variants) as formulas. Prefix with a single quote so the value
    is stored as text. Non-strings are returned unchanged.
    """
    if not isinstance(value, str) or not value:
        return value
    if value[0] in {"=", "+", "-", "@", "\t", "\r"}:
        return f"'{value}"
    return value


def csv_safe_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return a new dict with string values passed through :func:`csv_safe_cell`."""
    return {k: csv_safe_cell(v) for k, v in row.items()}


def csv_safe_rows(rows: list[MutableMapping[str, Any]] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [csv_safe_row(r) for r in rows]
