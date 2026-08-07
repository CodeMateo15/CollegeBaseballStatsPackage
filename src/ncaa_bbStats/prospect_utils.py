"""Read access to MLB Pipeline top-250 draft prospect rankings.

These are pre-draft scouting rankings, useful mainly as a benchmark: how a
consensus board compares against where players actually went, and against any
model's ordering.
"""

import csv
import os
from functools import lru_cache
from typing import Optional

from ncaa_bbStats._paths import data_path
from ncaa_bbStats.team_registry import as_team_id

__all__ = [
    "prospect_rank",
    "prospect_board",
    "prospect_vs_actual",
    "biggest_draft_risers",
    "biggest_draft_fallers",
    "available_seasons",
]

FIRST_SEASON = 2021
LAST_SEASON = 2026


@lru_cache(maxsize=8)
def _load(season: int) -> list:
    path = data_path("prospects", f"{season}.csv")
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = []
        for row in csv.DictReader(f):
            row["year"] = int(row["year"])
            row["rank"] = int(row["rank"]) if row["rank"] else None
            row["age"] = int(row["age"]) if row["age"] else None
            row["is_college"] = row["is_college"] == "True"
            rows.append(row)
    return rows


def available_seasons() -> list[int]:
    """Seasons with prospect rankings.

    Returns:
        list[int]: Sorted season years.
    """
    return [s for s in range(FIRST_SEASON, LAST_SEASON + 1) if _load(s)]


def prospect_rank(name: str, season: int) -> Optional[int]:
    """A player's pre-draft ranking on the top-250 board.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int): Draft year (2021-2026).

    Returns:
        int | None: The rank, or None if the player was not ranked.
    """
    for row in _load(season):
        if row["name"].lower() == name.lower():
            return row["rank"]
    return None


def prospect_board(
    season: int,
    *,
    n: Optional[int] = None,
    position: Optional[str] = None,
    team: Optional[str] = None,
    college_only: bool = False,
) -> list[dict]:
    """The prospect board for a draft year.

    Args:
        season (int): Draft year (2021-2026).
        n (int, optional): Return only the top N.
        position (str, optional): Filter by position, e.g. ``"RHP"``.
        team (str, optional): Any spelling of a college team name.
        college_only (bool): Exclude high-school prospects.

    Returns:
        list[dict]: Prospects in ranking order.
    """
    rows = _load(season)
    if college_only:
        rows = [r for r in rows if r["is_college"]]
    if position:
        rows = [r for r in rows if position.lower() in r["position"].lower()]
    if team:
        team_id = as_team_id(team)
        rows = [r for r in rows if r["team_id"] == team_id] if team_id else []
    rows = sorted(rows, key=lambda r: (r["rank"] is None, r["rank"]))
    return rows[:n] if n else rows


def prospect_vs_actual(season: int) -> list[dict]:
    """Pre-draft ranking against where each player was actually selected.

    A positive ``surprise`` means the player went earlier than the board had
    them; negative means they slid.

    Args:
        season (int): Draft year (2021-2026).

    Returns:
        list[dict]: ``name``, ``school``, ``prospect_rank``, ``actual_pick``,
        ``surprise``, for players who appear on both the board and the draft
        record, ordered by actual pick.
    """
    from ncaa_bbStats.draft_detail_utils import _load as _load_draft

    picks = {
        (p.get("name") or "").lower(): p
        for p in _load_draft(season)
        if p.get("pick")
    }

    out = []
    for row in _load(season):
        pick = picks.get(row["name"].lower())
        if not pick or row["rank"] is None:
            continue
        out.append({
            "name": row["name"],
            "school": row["school"],
            "position": row["position"],
            "is_college": row["is_college"],
            "prospect_rank": row["rank"],
            "actual_pick": pick["pick"],
            "surprise": row["rank"] - pick["pick"],
            "signing_bonus": pick["signing_bonus"],
        })
    return sorted(out, key=lambda r: r["actual_pick"])


def biggest_draft_risers(season: int, *, n: int = 15) -> list[dict]:
    """Players selected much earlier than their pre-draft ranking.

    Args:
        season (int): Draft year (2021-2026).
        n (int): How many to return.

    Returns:
        list[dict]: Rows from :func:`prospect_vs_actual`, biggest rise first.
    """
    rows = prospect_vs_actual(season)
    return sorted(rows, key=lambda r: -r["surprise"])[:n]


def biggest_draft_fallers(season: int, *, n: int = 15) -> list[dict]:
    """Players who slid well past their pre-draft ranking.

    Args:
        season (int): Draft year (2021-2026).
        n (int): How many to return.

    Returns:
        list[dict]: Rows from :func:`prospect_vs_actual`, biggest slide first.
    """
    rows = prospect_vs_actual(season)
    return sorted(rows, key=lambda r: r["surprise"])[:n]
