"""Internal helpers for locating and loading packaged data files.

Every module in the package resolves data through :func:`data_path` rather than
repeating the ``os.path.join(os.path.dirname(__file__), "..", "data", ...)``
idiom, so there is one place to change if the layout ever moves.

This module is private. Nothing here is re-exported from ``ncaa_bbStats``.
"""

import json
import os

__all__ = [
    "DATA_DIR",
    "data_path",
    "team_stats_path",
    "load_team_stats",
    "TEAM_STATS_SENTINEL_KEYS",
]

# src/ncaa_bbStats/_paths.py -> src/data
DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data")
)

# Keys that appear alongside team entries in the team-stats JSON files but are
# not teams. ``team_store.py`` writes ``"division": N`` at the end of every
# cache file; iterating ``stats.keys()`` without filtering it produces a team
# literally named "division", which is how rows like ``1056,division,1`` ended
# up in data/team_names_stats/all_div_teams.csv.
TEAM_STATS_SENTINEL_KEYS = frozenset({"division"})


def data_path(*parts: str) -> str:
    """Build an absolute path into the packaged ``src/data`` directory.

    Args:
        *parts: Path components relative to the data directory, e.g.
            ``data_path("team_stats_cache", "div1", "2025.json")``.

    Returns:
        str: The absolute path. The file is not required to exist.
    """
    return os.path.join(DATA_DIR, *parts)


def team_stats_path(year: int, division: int) -> str:
    """Return the cache path for one season of team stats.

    Args:
        year (int): The season year (ex. 2015).
        division (int): NCAA division number (1, 2, or 3).

    Returns:
        str: Absolute path to ``data/team_stats_cache/div{division}/{year}.json``.
    """
    return data_path("team_stats_cache", f"div{division}", f"{year}.json")


def load_team_stats(year: int, division: int) -> dict:
    """Load one season of cached team stats, without the bookkeeping keys.

    The returned mapping contains only team entries, keyed by
    ``"Team Name (League)"``. The ``"division"`` sentinel that ``team_store``
    appends to each cache file is removed.

    Args:
        year (int): The season year (ex. 2015).
        division (int): NCAA division number (1, 2, or 3).

    Returns:
        dict: Mapping of ``"Team (League)"`` to a dict of that team's stats.

    Raises:
        FileNotFoundError: If no cache file exists for that year and division.
    """
    file_path = team_stats_path(year, division)

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Stats for Division {division} in {year} not found.")

    with open(file_path, "r") as f:
        stats = json.load(f)

    return {
        team: values
        for team, values in stats.items()
        if team not in TEAM_STATS_SENTINEL_KEYS and isinstance(values, dict)
    }
