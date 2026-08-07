"""Questions that need several datasets at once.

Everything here is a hand-written join, not a generic query engine. Each function
answers one question well and reports which datasets it could and could not
reach, so a missing section reads as missing rather than as zero.

All of it depends on :mod:`ncaa_bbStats.team_registry` to reconcile the four
different ways these sources spell school names.
"""

from typing import Optional, Sequence

from ncaa_bbStats import team_registry as _registry
from ncaa_bbStats._paths import load_team_stats

__all__ = [
    "team_profile",
    "player_profile",
    "draft_yield",
    "dollars_per_draft_pick",
    "conference_report",
    "pipeline",
    "compare_teams",
]


def _team_stats_row(team_id: str, season: int) -> Optional[dict]:
    """The NCAA team-stats row for a program's season, if it has one."""
    division = _registry.team_division(team_id, season)
    if division is None:
        return None
    try:
        stats = load_team_stats(season, division)
    except FileNotFoundError:
        return None
    label = next(
        (s["ncaa_short"] for s in _registry.team_seasons(team_id)
         if s["season"] == season),
        None,
    )
    if label is None:
        return None
    for key, values in stats.items():
        if _registry.resolve_team(key) == team_id:
            return values
    return None


def team_profile(team: str, season: int) -> Optional[dict]:
    """Everything the package knows about one program in one season.

    Pulls identity, NCAA team statistics, RPI and schedule strength, conference,
    program finances, and that year's draft class into a single record. Sections
    the package cannot reach for that program are ``None`` rather than absent, so
    the shape is stable.

    Args:
        team (str): Any spelling of a team name.
        season (int): Season year.

    Returns:
        dict | None: Keys ``identity``, ``record``, ``stats``, ``rpi``,
        ``finance``, ``draft``, ``pythagorean``, and ``coverage``. None if the
        team cannot be resolved.
    """
    from ncaa_bbStats.draft_detail_utils import draft_class
    from ncaa_bbStats.program_utils import program_finance
    from ncaa_bbStats.rpi_utils import rpi_record
    from ncaa_bbStats.utils import get_pythagorean_expectation

    team_id = _registry.as_team_id(team)
    if team_id is None:
        return None

    identity = _registry.team_info(team_id, season=season)
    stats = _team_stats_row(team_id, season)
    rpi = rpi_record(team_id, season)
    finance = program_finance(team_id, season)
    draft = draft_class(team_id, season)

    record = None
    if stats:
        wins, losses = stats.get("W"), stats.get("L")
        if wins is not None and losses is not None:
            record = {
                "wins": wins,
                "losses": losses,
                "ties": stats.get("T", 0),
                "win_pct": stats.get("WPCT"),
            }

    pythagorean = None
    if identity and identity.get("division") and stats:
        value = get_pythagorean_expectation(
            identity["canonical_name"], season, identity["division"]
        )
        if isinstance(value, (int, float)):
            pythagorean = {
                "expected_win_pct": value,
                "actual_win_pct": stats.get("WPCT"),
                "luck": (
                    round(stats["WPCT"] - value, 4)
                    if stats.get("WPCT") is not None else None
                ),
            }

    return {
        "identity": identity,
        "record": record,
        "stats": stats,
        "rpi": rpi,
        "finance": finance,
        "draft": {
            "picks": len(draft),
            "selections": [
                {
                    "name": p["name"], "pick": p["pick"], "round": p["round"],
                    "position": p["position"], "signing_bonus": p["signing_bonus"],
                }
                for p in draft
            ],
        } if draft else None,
        "pythagorean": pythagorean,
        "coverage": {
            "stats": stats is not None,
            "rpi": rpi is not None,
            "finance": finance is not None,
            "draft": bool(draft),
        },
    }


def player_profile(name: str, season: Optional[int] = None) -> Optional[dict]:
    """Everything the package knows about one player.

    Combines their batting and pitching lines with their program's context and,
    if they were drafted, the draft record and pre-draft ranking.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int, optional): One season. Defaults to their most recent.

    Returns:
        dict | None: Keys ``name``, ``season``, ``batting``, ``pitching``,
        ``team``, ``draft``, ``prospect_rank``, ``coverage``. None if the player
        is not in the player cache.
    """
    from ncaa_bbStats.draft_detail_utils import _load as _load_draft
    from ncaa_bbStats.player_utils import get_player_rows, player_seasons
    from ncaa_bbStats.prospect_utils import prospect_rank

    batting_seasons = player_seasons("batting", "noMin", name)
    pitching_seasons = player_seasons("pitching", "noMin", name)
    all_seasons = sorted(set(batting_seasons) | set(pitching_seasons))
    if not all_seasons:
        return None

    season = season if season is not None else all_seasons[-1]

    batting = get_player_rows("batting", "noMin", name, year=season)
    pitching = get_player_rows("pitching", "noMin", name, year=season)

    team_context = None
    source = (batting or pitching)
    if source:
        acronym = source[0].get("team")
        team_id = _registry.resolve_team(acronym) if acronym else None
        if team_id:
            team_context = _registry.team_info(team_id, season=season)

    draft = None
    for draft_year in range(season, season + 3):
        match = next(
            (p for p in _load_draft(draft_year)
             if (p.get("name") or "").lower() == name.lower()),
            None,
        )
        if match:
            draft = match
            break

    return {
        "name": name,
        "season": season,
        "seasons_played": all_seasons,
        "role": (
            "two_way" if batting and pitching
            else "pitcher" if pitching else "batter"
        ),
        "batting": batting[0] if batting else None,
        "pitching": pitching[0] if pitching else None,
        "team": team_context,
        "draft": draft,
        "prospect_rank": (
            prospect_rank(name, draft["year"]) if draft else None
        ),
        "coverage": {
            "batting": bool(batting),
            "pitching": bool(pitching),
            "team": team_context is not None,
            "draft": draft is not None,
        },
    }


def draft_yield(team: str, start: int = 2021, end: int = 2026) -> Optional[dict]:
    """How many players a program put into the draft, and for how much.

    Args:
        team (str): Any spelling of a team name.
        start (int): First draft year.
        end (int): Last draft year.

    Returns:
        dict | None: ``picks``, ``picks_per_year``, ``top_ten_round_picks``,
        ``first_round_picks``, ``total_bonus_dollars``, ``best_pick``, and a
        per-year breakdown. None if the team cannot be resolved.
    """
    from ncaa_bbStats.draft_detail_utils import draft_class, round_number

    team_id = _registry.as_team_id(team)
    if team_id is None:
        return None

    by_year, all_picks = {}, []
    for season in range(start, end + 1):
        picks = draft_class(team_id, season)
        all_picks.extend(picks)
        by_year[season] = {
            "picks": len(picks),
            "bonus_dollars": sum(p.get("signing_bonus") or 0 for p in picks),
        }

    years = max(1, end - start + 1)
    ranked = [p for p in all_picks if p.get("pick")]
    return {
        "team_id": team_id,
        "team": _registry.team_info(team_id)["canonical_name"],
        "seasons": f"{start}-{end}",
        "picks": len(all_picks),
        "picks_per_year": round(len(all_picks) / years, 2),
        "first_round_picks": sum(1 for p in all_picks if round_number(p) == 1),
        "top_ten_round_picks": sum(
            1 for p in all_picks
            if (round_number(p) or 99) <= 10
        ),
        "total_bonus_dollars": sum(p.get("signing_bonus") or 0 for p in all_picks),
        "best_pick": min(ranked, key=lambda p: p["pick"], default=None),
        "by_year": by_year,
    }


def dollars_per_draft_pick(
    team: str, start: int = 2021, end: int = 2025
) -> Optional[dict]:
    """Program spending set against the players it produced.

    Budget is reported as a percentile rather than dollars, because the EADA
    survey's absolute figures are not comparable across years. So this is not a
    literal cost per pick -- it pairs spending rank with draft output, which is
    the comparison that actually travels.

    Args:
        team (str): Any spelling of a team name.
        start (int): First season.
        end (int): Last season. Defaults to 2025, the last surveyed year.

    Returns:
        dict | None: ``mean_budget_pct``, ``picks``, ``picks_per_year``,
        ``bonus_dollars_per_year``, ``seasons_with_finance``. None if the team
        cannot be resolved.
    """
    from ncaa_bbStats.program_utils import program_finance

    yield_ = draft_yield(team, start, end)
    if yield_ is None:
        return None

    percentiles = []
    for season in range(start, end + 1):
        finance = program_finance(yield_["team_id"], season)
        if finance and finance["budget_pct"] is not None:
            percentiles.append(finance["budget_pct"])

    years = max(1, end - start + 1)
    return {
        "team_id": yield_["team_id"],
        "team": yield_["team"],
        "seasons": f"{start}-{end}",
        "mean_budget_pct": (
            round(sum(percentiles) / len(percentiles), 4) if percentiles else None
        ),
        "seasons_with_finance": len(percentiles),
        "picks": yield_["picks"],
        "picks_per_year": yield_["picks_per_year"],
        "bonus_dollars_per_year": round(
            yield_["total_bonus_dollars"] / years, 2
        ),
    }


def conference_report(conference: str, season: int) -> dict:
    """A conference's members, results, spending, and draft output.

    Args:
        conference (str): Conference code, e.g. ``"SEC"``.
        season (int): Season year.

    Returns:
        dict: ``conference``, ``season``, ``programs``, ``standings``,
        ``draft_picks``, ``bonus_dollars``, ``median_budget_pct``,
        ``best_rpi_rank``.
    """
    from ncaa_bbStats.draft_detail_utils import conference_draft_counts
    from ncaa_bbStats.program_utils import conference_spending
    from ncaa_bbStats.rpi_utils import rpi_table

    teams = _registry.list_teams(season=season, conference=conference)
    standings = rpi_table(season, conference=conference)

    draft = next(
        (c for c in conference_draft_counts(season)
         if c["conference"].lower() == conference.lower()),
        None,
    )
    spending = next(
        (c for c in conference_spending(season)
         if c["conference"].lower() == conference.lower()),
        None,
    )

    return {
        "conference": conference,
        "season": season,
        "programs": len(teams),
        "members": [t["canonical_name"] for t in teams],
        "standings": [
            {
                "team": r["team_name"],
                "rpi_rank": r["rpi_rank"],
                "wins": r["overall_wins"],
                "losses": r["overall_losses"],
            }
            for r in standings
        ],
        "draft_picks": draft["picks"] if draft else None,
        "bonus_dollars": draft["bonus_dollars"] if draft else None,
        "median_budget_pct": spending["median_budget_pct"] if spending else None,
        "best_rpi_rank": (
            min((r["rpi_rank"] for r in standings if r["rpi_rank"]), default=None)
        ),
    }


def pipeline(team: str, start: int = 2021, end: int = 2026) -> list[dict]:
    """A program's season-by-season timeline across every dataset.

    One row per season: conference, record, RPI, budget percentile, and draft
    picks produced. Built for plotting a program's trajectory.

    Args:
        team (str): Any spelling of a team name.
        start (int): First season.
        end (int): Last season.

    Returns:
        list[dict]: One dict per season the program has any data for.
    """
    from ncaa_bbStats.draft_detail_utils import draft_class
    from ncaa_bbStats.program_utils import program_finance
    from ncaa_bbStats.rpi_utils import rpi_record

    team_id = _registry.as_team_id(team)
    if team_id is None:
        return []

    out = []
    for season in range(start, end + 1):
        stats = _team_stats_row(team_id, season)
        rpi = rpi_record(team_id, season)
        finance = program_finance(team_id, season)
        picks = draft_class(team_id, season)
        if not any((stats, rpi, finance, picks)):
            continue

        out.append({
            "season": season,
            "division": _registry.team_division(team_id, season),
            "conference": _registry.team_conference(team_id, season),
            "wins": stats.get("W") if stats else None,
            "losses": stats.get("L") if stats else None,
            "win_pct": stats.get("WPCT") if stats else None,
            "rpi_rank": rpi["rpi_rank"] if rpi else None,
            "sos_rank": rpi["sos_rank"] if rpi else None,
            "budget_pct": finance["budget_pct"] if finance else None,
            "draft_picks": len(picks),
            "bonus_dollars": sum(p.get("signing_bonus") or 0 for p in picks),
        })
    return out


def compare_teams(teams: Sequence[str], season: int) -> list[dict]:
    """Several programs side by side for one season.

    Args:
        teams (Sequence[str]): Team names in any spelling.
        season (int): Season year.

    Returns:
        list[dict]: One flat row per resolvable team, ordered as given.
    """
    rows = []
    for team in teams:
        profile = team_profile(team, season)
        if profile is None:
            continue
        identity = profile["identity"] or {}
        record = profile["record"] or {}
        rpi = profile["rpi"] or {}
        finance = profile["finance"] or {}
        rows.append({
            "team": identity.get("canonical_name"),
            "conference": identity.get("conference"),
            "division": identity.get("division"),
            "wins": record.get("wins"),
            "losses": record.get("losses"),
            "win_pct": record.get("win_pct"),
            "rpi_rank": rpi.get("rpi_rank"),
            "sos_rank": rpi.get("sos_rank"),
            "budget_pct": finance.get("budget_pct"),
            "draft_picks": profile["draft"]["picks"] if profile["draft"] else 0,
        })
    return rows
