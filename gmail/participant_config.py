"""Gmail pipeline accessors — loads shared config/participant.yaml."""

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
    first_name,
    last_name,
    load_participant_config,
    my_emails,
    participant_name,
    participant_name_patterns,
    search_window,
    source_config,
)

__all__ = [
    "CONFIG_PATH",
    "DEFAULT_SEARCH_WINDOW",
    "EXAMPLE_PATH",
    "first_name",
    "last_name",
    "load_participant_config",
    "my_emails",
    "participant_name",
    "participant_name_patterns",
    "search_window",
    "source_config",
]
