"""Read access to MLB Stats API draft records.

Adds the detail the Baseball Almanac cache does not carry: signing bonuses,
published slot values, school class, and player biography. Covers 2021-2026;
:mod:`ncaa_bbStats.utils` remains the way to reach 1965-2025 draft history.
"""

import json
import os
from functools import lru_cache
from typing import Optional

from ncaa_bbStats._paths import data_path
from ncaa_bbStats.team_registry import as_team_id, resolve_team, team_aliases

__all__ = [
    "draft_pick",
    "round_number",
    "round_label",
    "draft_class",
    "draft_board",
    "signing_bonus",
    "slot_value",
    "bonus_vs_slot",
    "overslot_picks",
    "biggest_bonuses",
    "draft_demographics",
    "conference_draft_counts",
    "state_pipeline",
    "available_seasons",
    "FIRST_SEASON",
    "LAST_SEASON",
]

FIRST_SEASON = 2021
LAST_SEASON = 2026

# school_class prefixes that mark a college player.
_COLLEGE_PREFIXES = ("4YR", "JC")

# Not every round is a number. Competitive-balance, supplemental, and prospect-
# promotion picks carry their own labels and slot in immediately after a numbered
# round -- 131 picks across 2021-2026. Anything calling int() on `round` breaks on
# them, and anything filtering "rounds 1 to 10" silently drops them.
_ROUND_LABELS = {
    "1C": 1,       # Competitive Balance Round A, after round 1
    "CB-A": 1,     # same, as the API spells it in other years
    "PPI": 1,      # Prospect Promotion Incentive, awarded after round 1
    "2C": 2,
    "CB-B": 2,     # Competitive Balance Round B, after round 2
    "SUP-2": 2,    # supplemental, after round 2
    "SUP-3": 3,
    "4C": 4,
}


@lru_cache(maxsize=8)
def _load(season: int) -> list:
    path = data_path("draft_detail", f"{season}.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def available_seasons() -> list[int]:
    """Seasons with detailed draft data.

    Returns:
        list[int]: Sorted season years.
    """
    return [s for s in range(FIRST_SEASON, LAST_SEASON + 1) if _load(s)]


def _is_college(pick: dict) -> bool:
    return (pick.get("school_class") or "").startswith(_COLLEGE_PREFIXES)


def round_number(pick: dict) -> Optional[int]:
    """The numbered round a pick belongs to, resolving compensation labels.

    A pick's ``round`` is usually a numeral, but competitive-balance,
    supplemental, and prospect-promotion selections carry labels like ``"CB-A"``,
    ``"SUP-2"``, and ``"PPI"``. Each falls immediately after a numbered round, so
    this maps them onto it -- otherwise they are dropped from any "first ten
    rounds" filter, which is where most of them sit.

    Args:
        pick (dict): A pick record.

    Returns:
        int | None: The round, or None if the label is unrecognised.
    """
    raw = str(pick.get("round") or "").strip().upper()
    if raw.isdigit():
        return int(raw)
    return _ROUND_LABELS.get(raw)


def round_label(pick: dict) -> str:
    """The round exactly as reported, including compensation labels.

    Args:
        pick (dict): A pick record.

    Returns:
        str: The label, e.g. ``"1"``, ``"CB-A"``, ``"PPI"``.
    """
    return str(pick.get("round") or "")


def draft_pick(season: int, pick: int) -> Optional[dict]:
    """Look up one pick by overall selection number.

    Args:
        season (int): Draft year (2021-2026).
        pick (int): Overall pick number, 1 being first.

    Returns:
        dict | None: The pick record, or None if not found.
    """
    return next((p for p in _load(season) if p["pick"] == pick), None)


def slot_value(season: int, pick: int) -> Optional[int]:
    """The published bonus slot value for a pick, in dollars.

    Slot values are assigned by MLB for the first ten rounds. Picks after round
    ten have no published slot -- those return ``None`` rather than zero, which
    is what the API literally reports.

    Args:
        season (int): Draft year (2021-2026).
        pick (int): Overall pick number.

    Returns:
        int | None: Dollars, or None if the pick has no published slot.
    """
    record = draft_pick(season, pick)
    return record["slot_value"] if record else None


def signing_bonus(name: str, season: int) -> Optional[int]:
    """A drafted player's signing bonus, in dollars.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int): Draft year (2021-2026).

    Returns:
        int | None: Dollars, or None if the player is not found or did not sign.
    """
    for pick in _load(season):
        if (pick.get("name") or "").lower() == name.lower():
            return pick["signing_bonus"]
    return None


def bonus_vs_slot(name: str, season: int) -> Optional[float]:
    """Ratio of a player's signing bonus to their pick's slot value.

    Above 1.0 means they signed over slot -- usually a player who had leverage,
    such as college eligibility remaining. Below 1.0 means under slot, which
    often funds an over-slot pick elsewhere in the same class.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int): Draft year (2021-2026).

    Returns:
        float | None: The ratio, or None if either figure is missing.
    """
    for pick in _load(season):
        if (pick.get("name") or "").lower() != name.lower():
            continue
        bonus, slot = pick["signing_bonus"], pick["slot_value"]
        if bonus is None or not slot:
            return None
        return round(bonus / slot, 4)
    return None


def draft_class(team: str, season: int) -> list[dict]:
    """Every player drafted out of a program in one year.

    Args:
        team (str): Any spelling of a college team name.
        season (int): Draft year (2021-2026).

    Returns:
        list[dict]: Picks, ordered by selection number.
    """
    team_id = as_team_id(team)
    if team_id is None:
        return []
    names = {a.lower() for a in team_aliases(team_id)}
    return [
        p for p in _load(season)
        if (p.get("school") or "").lower() in names
        or resolve_team(p.get("school") or "") == team_id
    ]


def draft_history(
    team: str, start: int = FIRST_SEASON, end: int = LAST_SEASON
) -> list[dict]:
    """Every player drafted out of a program across several years.

    Args:
        team (str): Any spelling of a college team name.
        start (int): First draft year.
        end (int): Last draft year.

    Returns:
        list[dict]: Picks, ordered by year then selection number.
    """
    out = []
    for season in range(start, end + 1):
        out.extend(draft_class(team, season))
    return out


def draft_board(
    season: int, *, n: Optional[int] = None, college_only: bool = False
) -> list[dict]:
    """The draft in selection order.

    Args:
        season (int): Draft year (2021-2026).
        n (int, optional): Return only the first N picks.
        college_only (bool): Exclude high-school selections.

    Returns:
        list[dict]: Picks in order.
    """
    picks = [p for p in _load(season) if not college_only or _is_college(p)]
    return picks[:n] if n else picks


def biggest_bonuses(season: int, *, n: int = 25) -> list[dict]:
    """The largest signing bonuses in a draft class.

    Args:
        season (int): Draft year (2021-2026).
        n (int): How many to return.

    Returns:
        list[dict]: Picks sorted by bonus, largest first.
    """
    picks = [p for p in _load(season) if p["signing_bonus"]]
    picks.sort(key=lambda p: -p["signing_bonus"])
    return picks[:n]


def overslot_picks(
    season: int, *, min_ratio: float = 1.05, n: Optional[int] = None
) -> list[dict]:
    """Players who signed for meaningfully more than their pick's slot value.

    Args:
        season (int): Draft year (2021-2026).
        min_ratio (float): Minimum bonus-to-slot ratio to include.
        n (int, optional): Return only the top N.

    Returns:
        list[dict]: Picks with a ``bonus_slot_ratio`` field, largest first.
    """
    out = []
    for pick in _load(season):
        bonus, slot = pick["signing_bonus"], pick["slot_value"]
        if bonus is None or not slot:
            continue
        ratio = bonus / slot
        if ratio >= min_ratio:
            out.append(dict(pick, bonus_slot_ratio=round(ratio, 4)))
    out.sort(key=lambda p: -p["bonus_slot_ratio"])
    return out[:n] if n else out


def draft_demographics(season: int) -> dict:
    """Summary of who was taken in a draft class.

    Args:
        season (int): Draft year (2021-2026).

    Returns:
        dict: Counts by origin (four-year college, junior college, high school),
        by class, by position, plus mean age and total bonus dollars.
    """
    picks = _load(season)
    if not picks:
        return {}

    origins, classes, positions, states = {}, {}, {}, {}
    ages, bonuses = [], []
    for pick in picks:
        school_class = pick.get("school_class") or ""
        origin = (
            "four_year" if school_class.startswith("4YR")
            else "junior_college" if school_class.startswith("JC")
            else "high_school_or_other"
        )
        origins[origin] = origins.get(origin, 0) + 1
        if school_class:
            classes[school_class] = classes.get(school_class, 0) + 1
        if pick.get("position"):
            positions[pick["position"]] = positions.get(pick["position"], 0) + 1
        if pick.get("school_state"):
            states[pick["school_state"]] = states.get(pick["school_state"], 0) + 1
        if pick.get("age"):
            ages.append(pick["age"])
        if pick.get("signing_bonus"):
            bonuses.append(pick["signing_bonus"])

    return {
        "season": season,
        "picks": len(picks),
        "by_origin": dict(sorted(origins.items(), key=lambda kv: -kv[1])),
        "by_class": dict(sorted(classes.items(), key=lambda kv: -kv[1])),
        "by_position": dict(sorted(positions.items(), key=lambda kv: -kv[1])),
        "top_states": dict(sorted(states.items(), key=lambda kv: -kv[1])[:10]),
        "mean_age": round(sum(ages) / len(ages), 2) if ages else None,
        "signed": len(bonuses),
        "total_bonus_dollars": sum(bonuses),
    }


def conference_draft_counts(season: int, *, division: int = 1) -> list[dict]:
    """How many players each conference produced in a draft class.

    Args:
        season (int): Draft year (2021-2026).
        division (int): NCAA division to attribute programs by.

    Returns:
        list[dict]: ``conference``, ``picks``, ``bonus_dollars``, sorted by picks.
    """
    from ncaa_bbStats.team_registry import team_conference

    counts = {}
    for pick in _load(season):
        if not _is_college(pick):
            continue
        team_id = resolve_team(pick.get("school") or "")
        if team_id is None:
            continue
        # The player's college season is the spring of the draft year.
        conference = team_conference(team_id, season)
        if not conference:
            continue
        entry = counts.setdefault(
            conference, {"conference": conference, "picks": 0, "bonus_dollars": 0}
        )
        entry["picks"] += 1
        entry["bonus_dollars"] += pick.get("signing_bonus") or 0

    return sorted(counts.values(), key=lambda c: -c["picks"])


def state_pipeline(
    state: str, *, start: int = FIRST_SEASON, end: int = LAST_SEASON
) -> list[dict]:
    """Players drafted out of schools in one state, by year.

    Args:
        state (str): Two-letter state code, e.g. ``"TX"``.
        start (int): First draft year.
        end (int): Last draft year.

    Returns:
        list[dict]: One dict per year with ``picks`` and ``bonus_dollars``.
    """
    out = []
    for season in range(start, end + 1):
        picks = [
            p for p in _load(season)
            if (p.get("school_state") or "").upper() == state.upper()
        ]
        if not picks:
            continue
        out.append({
            "season": season,
            "picks": len(picks),
            "bonus_dollars": sum(p.get("signing_bonus") or 0 for p in picks),
            "top_pick": min(
                (p for p in picks if p.get("pick")),
                key=lambda p: p["pick"],
                default=None,
            ),
        })
    return out
