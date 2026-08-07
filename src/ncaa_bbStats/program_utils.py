"""Read access to baseball program finances, from the federal EADA survey.

Coverage is 2021-2025 with 2025 carried forward to 2026, and about 99% of
Division I. Every function that returns a season's figures reports whether they
were carried forward, because a carried-forward number quietly treated as
current is how wrong conclusions get published.
"""

import csv
import os
from functools import lru_cache
from typing import Optional

from ncaa_bbStats._paths import data_path
from ncaa_bbStats.team_registry import as_team_id, team_conference

__all__ = [
    "program_finance",
    "budget_percentile",
    "roster_size",
    "coaching_staff_size",
    "richest_programs",
    "finance_vs_rpi",
    "conference_spending",
    "available_seasons",
]

FEATURE_COLUMNS = (
    "budget_pct", "log_budget", "opex_per_player_pct", "log_opex_per_player",
    "log_budget_per_player", "roster_size", "log_revenue", "net_revenue",
    "coaching_staff_size", "dept_recruiting_pct", "log_dept_recruiting",
    "log_dept_coach_salary",
)


@lru_cache(maxsize=1)
def _load() -> dict:
    """Load the derived features, keyed by (team_id, season)."""
    path = data_path("program_finance", "eada_features.csv")
    if not os.path.isfile(path):
        return {}

    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            season = int(row["season"])
            row["season"] = season
            row["eada_year"] = int(row["eada_year"])
            row["carried_forward"] = row["carried_forward"] == "True"
            for column in FEATURE_COLUMNS:
                value = row.get(column)
                row[column] = float(value) if value not in (None, "") else None
            rows[(row["team_id"], season)] = row
    return rows


@lru_cache(maxsize=1)
def available_seasons() -> tuple:
    """Seasons with program-finance data.

    Returns:
        tuple[int, ...]: Sorted season years.
    """
    return tuple(sorted({season for _team, season in _load()}))


def program_finance(team: str, season: int) -> Optional[dict]:
    """A program's baseball finances for one season.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        dict | None: The twelve derived features plus ``eada_year`` and
        ``carried_forward``. None if the program has no filing that season.

    Note:
        For 2026, ``carried_forward`` is True and ``eada_year`` is 2025:
        institutions file the 2025-26 survey in October 2026, so no figures for
        that season exist yet.
    """
    team_id = as_team_id(team)
    if team_id is None:
        return None
    row = _load().get((team_id, season))
    return dict(row) if row else None


def budget_percentile(team: str, season: int) -> Optional[float]:
    """Where a program's baseball budget ranks among all filers that year.

    Expressed as a percentile in [0, 1], so 0.95 means it outspends 95% of
    programs. Percentiles rather than dollars, because budgets inflate a few
    percent a year and raw figures are not comparable across seasons.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        float | None: The percentile, or None if unavailable.
    """
    row = program_finance(team, season)
    return row["budget_pct"] if row else None


def roster_size(team: str, season: int) -> Optional[float]:
    """Number of baseball participants a program reported.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        float | None: Participants, or None if unreported or implausible. A few
        institutions file a system-wide row summing every branch campus; those
        are treated as unreported rather than believed.
    """
    row = program_finance(team, season)
    return row["roster_size"] if row else None


def coaching_staff_size(team: str, season: int) -> Optional[float]:
    """Head plus assistant baseball coaches a program reported.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year (2021-2026).

    Returns:
        float | None: Coach count, or None if unavailable.
    """
    row = program_finance(team, season)
    return row["coaching_staff_size"] if row else None


def richest_programs(
    season: int, *, n: int = 25, division: Optional[int] = None
) -> list[dict]:
    """The highest-spending baseball programs in a season.

    Args:
        season (int): Season year (2021-2026).
        n (int): How many to return.
        division (int, optional): Restrict to one NCAA division.

    Returns:
        list[dict]: ``team_id``, ``institution_name``, ``budget_pct``,
        ``roster_size``, ``coaching_staff_size``, sorted by budget.
    """
    from ncaa_bbStats.team_registry import team_division

    rows = [
        r for (team_id, row_season), r in _load().items()
        if row_season == season and r["budget_pct"] is not None
    ]
    if division is not None:
        rows = [r for r in rows if team_division(r["team_id"], season) == division]

    rows.sort(key=lambda r: -r["budget_pct"])
    return [
        {
            "team_id": r["team_id"],
            "institution_name": r["institution_name"],
            "budget_pct": r["budget_pct"],
            "roster_size": r["roster_size"],
            "coaching_staff_size": r["coaching_staff_size"],
            "carried_forward": r["carried_forward"],
        }
        for r in rows[:n]
    ]


def conference_spending(season: int, *, division: int = 1) -> list[dict]:
    """Median baseball budget percentile by conference.

    Args:
        season (int): Season year (2021-2026).
        division (int): NCAA division.

    Returns:
        list[dict]: ``conference``, ``programs``, ``median_budget_pct``, sorted
        by spending, richest first.
    """
    by_conference = {}
    for (team_id, row_season), row in _load().items():
        if row_season != season or row["budget_pct"] is None:
            continue
        conference = team_conference(team_id, season)
        if not conference:
            continue
        by_conference.setdefault(conference, []).append(row["budget_pct"])

    out = []
    for conference, values in by_conference.items():
        values.sort()
        middle = len(values) // 2
        median = (
            values[middle] if len(values) % 2
            else (values[middle - 1] + values[middle]) / 2
        )
        out.append({
            "conference": conference,
            "programs": len(values),
            "median_budget_pct": round(median, 4),
        })
    return sorted(out, key=lambda c: -c["median_budget_pct"])


def finance_vs_rpi(season: int, *, division: int = 1) -> list[dict]:
    """Program spending beside on-field results, ready for correlation work.

    Args:
        season (int): Season year (2021-2026).
        division (int): NCAA division.

    Returns:
        list[dict]: One row per program with both a budget percentile and an RPI
        rank: ``team_id``, ``institution_name``, ``conference``, ``budget_pct``,
        ``rpi_rank``, ``win_pct``.
    """
    from ncaa_bbStats.rpi_utils import _load as _load_rpi
    from ncaa_bbStats.team_registry import team_division

    rpi_rows = _load_rpi(season)
    out = []
    for (team_id, row_season), row in _load().items():
        if row_season != season or row["budget_pct"] is None:
            continue
        if team_division(team_id, season) != division:
            continue
        rpi_row = rpi_rows.get(team_id)
        if not rpi_row:
            continue
        out.append({
            "team_id": team_id,
            "institution_name": row["institution_name"],
            "conference": rpi_row["conference"],
            "budget_pct": row["budget_pct"],
            "rpi_rank": rpi_row["rpi_rank"],
            "win_pct": rpi_row["overall_win_pct"],
        })
    return sorted(out, key=lambda r: r["rpi_rank"] or 9999)
