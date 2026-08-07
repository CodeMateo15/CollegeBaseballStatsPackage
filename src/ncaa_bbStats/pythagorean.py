"""Pythagorean expectation and the luck it exposes.

A team's Pythagorean expectation estimates the record its run scoring and run
prevention imply. Teams far above it won more close games than their run
differential justifies, which historically does not repeat -- so the gap is one
of the more useful signals for whether a season is likely to be sustained.

The standard exponent is 1.83. Per-conference exponents fitted to NCAA data ship
here as well, but they are **experimental and not the default**: fitting moves
the exponent between 1.45 and 2.08, yet not one of the 31 conference fits differs
from 1.83 at p < 0.05. Defaulting to them would present noise as precision.
"""

import csv
import os
from functools import lru_cache
from typing import Optional

from ncaa_bbStats._paths import data_path, load_team_stats
from ncaa_bbStats._normalize import split_team_league
from ncaa_bbStats.utils import PYTHAGOREAN_EXPONENT, get_pythagorean_expectation

__all__ = [
    "pythagorean_exponent",
    "conference_exponents",
    "luck_rating",
    "luckiest_teams",
    "unluckiest_teams",
    "PYTHAGOREAN_EXPONENT",
]


@lru_cache(maxsize=1)
def _exponents() -> dict:
    path = data_path("pythagorean", "conference_exponents.csv")
    if not os.path.isfile(path):
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        rows = {}
        for row in csv.DictReader(f):
            for key in ("exponent", "r2_fitted", "r2_default", "rmse_fitted",
                        "rmse_default", "p_value"):
                row[key] = float(row[key]) if row[key] else None
            row["n_team_seasons"] = int(row["n_team_seasons"])
            rows[row["conference"].lower()] = row
    return rows


def pythagorean_exponent(
    conference: Optional[str] = None, *, default: float = PYTHAGOREAN_EXPONENT
) -> float:
    """The Pythagorean exponent to use, optionally fitted to a conference.

    Args:
        conference (str, optional): Conference code, e.g. ``"SEC"``. If omitted
            or unknown, returns the default.
        default (float): Value to return when no fitted exponent applies.

    Returns:
        float: The exponent.

    Note:
        Conference-fitted exponents are experimental. None differs from 1.83 at
        p < 0.05, so prefer the default unless you are specifically exploring
        conference effects.
    """
    if not conference:
        return default
    row = _exponents().get(conference.lower())
    return row["exponent"] if row else default


def conference_exponents() -> list[dict]:
    """Every fitted per-conference exponent, with its diagnostics.

    Returns:
        list[dict]: ``conference``, ``exponent``, ``n_team_seasons``,
        ``r2_fitted``, ``r2_default``, ``rmse_fitted``, ``rmse_default``,
        ``p_value``, ``significant``. Sorted by exponent, largest first.

        ``significant`` is ``"no"`` for every conference: the improvement from
        fitting is never distinguishable from chance.
    """
    return sorted(_exponents().values(), key=lambda r: -r["exponent"])


def luck_rating(
    team: str, year: int, division: int = 1, *, conference_calibrated: bool = False
) -> Optional[dict]:
    """How much a team over- or under-performed its run differential.

    Args:
        team (str): Team name or substring.
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).
        conference_calibrated (bool): Use the experimental conference exponent.

    Returns:
        dict | None: ``expected_win_pct``, ``actual_win_pct``, ``luck`` (actual
        minus expected), and ``luck_wins`` (that gap expressed in games). None if
        the team has no run or record data that season.
    """
    from ncaa_bbStats.utils import get_team_stat

    expected = get_pythagorean_expectation(
        team, year, division, conference_calibrated=conference_calibrated
    )
    if not isinstance(expected, (int, float)):
        return None

    wins = get_team_stat("W", team, year, division)
    losses = get_team_stat("L", team, year, division)
    ties = get_team_stat("T", team, year, division) or 0
    if wins is None or losses is None:
        return None

    games = wins + losses + ties
    if games <= 0:
        return None

    actual = wins / games
    return {
        "team": team,
        "year": year,
        "expected_win_pct": expected,
        "actual_win_pct": round(actual, 4),
        "luck": round(actual - expected, 4),
        "luck_wins": round((actual - expected) * games, 2),
        "games": games,
    }


def _season_luck(year: int, division: int, conference_calibrated: bool) -> list[dict]:
    """Luck ratings for every team in a season."""
    try:
        teams = load_team_stats(year, division)
    except FileNotFoundError:
        return []

    out = []
    for label, stats in teams.items():
        runs, runs_allowed = stats.get("R (Batting)"), stats.get("R (Pitching)")
        wins, losses = stats.get("W"), stats.get("L")
        if None in (runs, runs_allowed, wins, losses) or not (runs or runs_allowed):
            continue

        exponent = PYTHAGOREAN_EXPONENT
        if conference_calibrated:
            exponent = pythagorean_exponent(split_team_league(label)[1])

        try:
            expected = runs ** exponent / (runs ** exponent + runs_allowed ** exponent)
        except (ZeroDivisionError, ValueError, OverflowError):
            continue

        games = wins + losses + (stats.get("T") or 0)
        if games <= 0:
            continue
        actual = wins / games

        out.append({
            "team": split_team_league(label)[0],
            "conference": split_team_league(label)[1],
            "year": year,
            "expected_win_pct": round(expected, 4),
            "actual_win_pct": round(actual, 4),
            "luck": round(actual - expected, 4),
            "luck_wins": round((actual - expected) * games, 2),
            "games": games,
        })
    return out


def luckiest_teams(
    year: int, division: int = 1, *, n: int = 10, conference_calibrated: bool = False
) -> list[dict]:
    """Teams that most outperformed their run differential.

    Args:
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).
        n (int): How many teams to return.
        conference_calibrated (bool): Use the experimental conference exponent.

    Returns:
        list[dict]: Sorted by wins above expectation, largest first.
    """
    rows = _season_luck(year, division, conference_calibrated)
    return sorted(rows, key=lambda r: -r["luck_wins"])[:n]


def unluckiest_teams(
    year: int, division: int = 1, *, n: int = 10, conference_calibrated: bool = False
) -> list[dict]:
    """Teams that most underperformed their run differential.

    Args:
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).
        n (int): How many teams to return.
        conference_calibrated (bool): Use the experimental conference exponent.

    Returns:
        list[dict]: Sorted by wins below expectation, largest shortfall first.
    """
    rows = _season_luck(year, division, conference_calibrated)
    return sorted(rows, key=lambda r: r["luck_wins"])[:n]
