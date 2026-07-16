"""LinkedIn pipeline accessors — loads shared config/participant.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from common.participant_config import (  # noqa: E402
    CONFIG_PATH,
    DEFAULT_SEARCH_WINDOW,
    EXAMPLE_PATH,
    linkedin_display_name,
    load_participant_config,
    participant_name,
    search_window,
    source_config,
    summary_window,
)

# Back-compat alias used by dump_threads / stats
participant_display_name = linkedin_display_name

__all__ = [
    "CONFIG_PATH",
    "DEFAULT_SEARCH_WINDOW",
    "EXAMPLE_PATH",
    "linkedin_display_name",
    "load_participant_config",
    "participant_display_name",
    "participant_name",
    "search_window",
    "source_config",
    "summary_window",
]
