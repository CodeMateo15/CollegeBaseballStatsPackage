"""Read access to RPI, strength of schedule, and quadrant records.

RPI is Warren Nolan's computation from public game results, not an official NCAA
statistic. Coverage is Division I from 2021; the site does not publish earlier
years, so functions return ``None`` outside that range rather than raising --
the gap is permanent, not a backlog.

Note that RPI and SOS are stored as **ranks**, where 1 is best.
"""

import csv
import os
from functools import lru_cache
from typing import Optional

from ncaa_bbStats._paths import data_path
from ncaa_bbStats.team_registry import as_team_id

__all__ = [
    "rpi",
    "rpi_rank",
    "strength_of_schedule",
    "rpi_table",
    "rpi_record",
    "quadrant_record",
    "home_road_neutral",
    "nonconference_profile",
    "rpi_over_years",
    "best_wins",
    "available_seasons",
]

FIRST_SEASON = 2021
LAST_SEASON = 2026

_QUADRANTS = (1, 2, 3, 4)
_NUMERIC_SUFFIXES = ("_wins", "_losses", "_win_pct")


@lru_cache(maxsize=8)
def _load(season: int) -> dict:
    """Load one season, keyed by team_id. Empty if the season is not covered."""
    path = data_path("rpi", f"{season}.csv")
    if not os.path.isfile(path):
        return {}

    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key, value in list(row.items()):
                if key in ("team_id", "team_name", "conference"):
                    continue
                if value == "":
                    row[key] = None
                elif key.endswith("_win_pct"):
                    row[key] = float(value)
                else:
                    row[key] = int(float(value))
            rows[row["team_id"]] = row
    return rows


def available_seasons() -> list[int]:
    """Seasons with RPI data.

    Returns:
        list[int]: Sorted season years.
    """
    return [s for s in range(FIRST_SEASON, LAST_SEASON + 1) if _load(s)]


def _row(team: str, season: int) -> Optional[dict]:
    team_id = as_team_id(team)
    if team_id is None:
        return None
    return _load(season).get(team_id)


def rpi_rank(team: str, season: int) -> Optional[int]:
    """A team's RPI rank, where 1 is the best in Division I.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        int | None: The rank, or None if the team or season has no record.
    """
    row = _row(team, season)
    return row["rpi_rank"] if row else None


#: Alias for :func:`rpi_rank`, since "RPI" is commonly used to mean the rank.
rpi = rpi_rank


def strength_of_schedule(team: str, season: int) -> Optional[int]:
    """A team's strength-of-schedule rank, where 1 is the toughest schedule.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        int | None: The rank, or None if unavailable.
    """
    row = _row(team, season)
    return row["sos_rank"] if row else None


def rpi_record(team: str, season: int) -> Optional[dict]:
    """A team's full RPI profile for one season.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        dict | None: Every stored field, including ranks, splits, and quadrant
        records. None if unavailable.
    """
    row = _row(team, season)
    return dict(row) if row else None


def quadrant_record(team: str, season: int, quadrant: int) -> Optional[dict]:
    """A team's record against one quadrant of opponents.

    Quadrants group opponents by strength, Q1 being the toughest. A team's Q1
    record is the usual shorthand for how it fared against good teams.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).
        quadrant (int): 1, 2, 3, or 4.

    Returns:
        dict | None: ``wins``, ``losses``, ``win_pct``. None if unavailable.
    """
    if quadrant not in _QUADRANTS:
        raise ValueError(f"quadrant must be one of {_QUADRANTS}, got {quadrant}")
    row = _row(team, season)
    if not row:
        return None
    return {
        "wins": row[f"q{quadrant}_wins"],
        "losses": row[f"q{quadrant}_losses"],
        "win_pct": row[f"q{quadrant}_win_pct"],
    }


def home_road_neutral(team: str, season: int) -> Optional[dict]:
    """A team's home, road, and neutral-site records.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        dict | None: One entry per venue type, each with ``wins``, ``losses``,
        ``win_pct``. None if unavailable.
    """
    row = _row(team, season)
    if not row:
        return None
    return {
        venue: {
            "wins": row[f"{venue}_wins"],
            "losses": row[f"{venue}_losses"],
            "win_pct": row[f"{venue}_win_pct"],
        }
        for venue in ("home", "road", "neutral")
    }


def nonconference_profile(team: str, season: int) -> Optional[dict]:
    """A team's non-conference record and how hard that schedule was.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        dict | None: ``wins``, ``losses``, ``win_pct``, ``rpi_rank``,
        ``sos_rank``. None if unavailable.
    """
    row = _row(team, season)
    if not row:
        return None
    return {
        "wins": row["nonconference_wins"],
        "losses": row["nonconference_losses"],
        "win_pct": row["nonconference_win_pct"],
        "rpi_rank": row["nonconference_rpi_rank"],
        "sos_rank": row["nonconference_sos_rank"],
    }


def rpi_table(
    season: int,
    *,
    conference: Optional[str] = None,
    n: Optional[int] = None,
) -> list[dict]:
    """The RPI standings for a season.

    Args:
        season (int): Season year (2021-2026).
        conference (str, optional): Restrict to one conference.
        n (int, optional): Return only the top N.

    Returns:
        list[dict]: Rows ordered by RPI rank, best first.
    """
    rows = [dict(r) for r in _load(season).values()]
    if conference:
        rows = [r for r in rows if r["conference"].lower() == conference.lower()]
    rows.sort(key=lambda r: (r["rpi_rank"] is None, r["rpi_rank"]))
    return rows[:n] if n else rows


def rpi_over_years(
    team: str, start: int = FIRST_SEASON, end: int = LAST_SEASON
) -> list[dict]:
    """A team's RPI and schedule strength season by season.

    Args:
        team (str): Any spelling of a team name.
        start (int): First season.
        end (int): Last season.

    Returns:
        list[dict]: One dict per season with data, sorted by season.
    """
    out = []
    for season in range(start, end + 1):
        row = _row(team, season)
        if not row:
            continue
        out.append({
            "season": season,
            "rpi_rank": row["rpi_rank"],
            "sos_rank": row["sos_rank"],
            "conference": row["conference"],
            "wins": row["overall_wins"],
            "losses": row["overall_losses"],
            "win_pct": row["overall_win_pct"],
        })
    return out


def best_wins(season: int, *, n: int = 25) -> list[dict]:
    """Teams with the most Quadrant 1 wins -- the best wins against good teams.

    Args:
        season (int): Season year (2021-2026).
        n (int): How many teams to return.

    Returns:
        list[dict]: ``team_id``, ``team_name``, ``conference``, ``q1_wins``,
        ``q1_losses``, ``rpi_rank``, sorted by Q1 wins.
    """
    rows = [
        {
            "team_id": r["team_id"],
            "team_name": r["team_name"],
            "conference": r["conference"],
            "q1_wins": r["q1_wins"],
            "q1_losses": r["q1_losses"],
            "rpi_rank": r["rpi_rank"],
        }
        for r in _load(season).values()
        if r["q1_wins"] is not None
    ]
    rows.sort(key=lambda r: (-r["q1_wins"], r["rpi_rank"] or 9999))
    return rows[:n]
