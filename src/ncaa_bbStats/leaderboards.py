"""Leaderboards over player seasons and careers.

Replaces :func:`ncaa_bbStats.player_utils.top_players`, which sorts descending
unconditionally -- so asking it for the top ERA returns the worst pitchers in
the country -- always reads the qualified population, and offers no playing-time
control beyond that.
"""

from typing import Literal, Optional, Sequence

import pandas as pd

from ncaa_bbStats.advanced_stats import add_advanced_columns, ip_to_float
from ncaa_bbStats.player_utils import StatType, Qualifier, _load_df
from ncaa_bbStats.team_registry import as_team_id, resolve_team, team_conference

__all__ = [
    "leaderboard",
    "stat_direction",
    "qualification_rules",
    "LOWER_IS_BETTER",
]

#: Statistics where a smaller value is a better performance. Everything not
#: listed here sorts descending. Exposed so the assumption is inspectable rather
#: than buried -- pass ``ascending=`` to override for any stat.
LOWER_IS_BETTER = frozenset({
    # Pitching
    "era", "whip", "cfip", "e-cf", "bb/9", "hr/9", "l", "r", "er", "h", "hr",
    "bb", "hbp", "wp", "bk", "bb%", "avg", "babip",
    # Batting
    "so", "k%", "cs", "gdp",
})

#: Statistics that are shared between batting and pitching but point opposite
#: ways. A pitcher wants strikeouts high; a batter wants them low.
_DIRECTION_BY_TYPE = {
    ("pitching", "so"): "higher",
    ("pitching", "k%"): "higher",
    ("pitching", "k/9"): "higher",
    ("pitching", "sho"): "higher",
    ("pitching", "cg"): "higher",
    ("batting", "r"): "higher",
    ("batting", "h"): "higher",
    ("batting", "hr"): "higher",
    ("batting", "bb"): "higher",
    ("batting", "hbp"): "higher",
    ("batting", "avg"): "higher",
    ("batting", "babip"): "higher",
    ("batting", "bb%"): "higher",
}

# Qualification thresholds, per team game.
_PA_PER_GAME = 3.1
_IP_PER_GAME = 1.0
# A full NCAA regular season. Used only to express the thresholds in the docs;
# the `qualified` flag in the cache is the actual authority.
_TYPICAL_SEASON_GAMES = 56


def stat_direction(stat: str, stat_type: StatType = "batting") -> str:
    """Whether a higher or lower value is the better performance.

    Args:
        stat (str): Column name, matched case-insensitively.
        stat_type (str): ``"batting"`` or ``"pitching"``. Needed because some
            stats point opposite ways -- strikeouts are good for a pitcher and
            bad for a hitter.

    Returns:
        str: ``"higher"`` or ``"lower"``.
    """
    key = stat.strip().lower()
    override = _DIRECTION_BY_TYPE.get((stat_type, key))
    if override:
        return override
    return "lower" if key in LOWER_IS_BETTER else "higher"


def qualification_rules(stat_type: StatType, year: Optional[int] = None) -> dict:
    """The playing-time minimums behind ``qualifier="qualified"``.

    Qualification is per team game, so the absolute threshold varies with how
    many games a team played. The cache carries the resulting flag directly; the
    numbers here explain what it means.

    Args:
        stat_type (str): ``"batting"`` or ``"pitching"``.
        year (int, optional): Season, for context only.

    Returns:
        dict: ``per_game``, ``basis``, ``typical_season_games``, and the implied
        ``typical_threshold``.
    """
    per_game = _PA_PER_GAME if stat_type == "batting" else _IP_PER_GAME
    basis = "plate appearances" if stat_type == "batting" else "innings pitched"
    return {
        "stat_type": stat_type,
        "year": year,
        "per_game": per_game,
        "basis": basis,
        "typical_season_games": _TYPICAL_SEASON_GAMES,
        "typical_threshold": round(per_game * _TYPICAL_SEASON_GAMES, 1),
    }


def _career_frame(df: pd.DataFrame, stat_type: StatType) -> pd.DataFrame:
    """Aggregate seasons into career totals, re-deriving the rates."""
    counting = [
        c for c in df.columns
        if c not in {"player_id", "name", "team", "team name", "division",
                     "year", "age", "qualified"}
        and pd.api.types.is_numeric_dtype(df[c])
    ]

    grouped = df.groupby("name", as_index=False)
    totals = grouped[counting].sum(numeric_only=True)

    # Innings are base-3: sum true innings, then convert back to NCAA notation
    # so the rate helpers parse them correctly.
    if "ip" in df.columns:
        innings = grouped["ip"].apply(
            lambda s: sum(ip_to_float(v) or 0.0 for v in s)
        )
        outs = (innings["ip"] * 3).round().astype(int)
        totals["ip"] = outs // 3 + (outs % 3) / 10.0

    context = grouped.agg(
        team=("team", "last"),
        year=("year", "max"),
        seasons=("year", "nunique"),
    )
    out = totals.merge(context, on="name")
    return add_advanced_columns(out, stat_type)


def leaderboard(
    stat: str,
    *,
    stat_type: StatType = "batting",
    year: Optional[int] = None,
    years: Optional[Sequence[int]] = None,
    team: Optional[str] = None,
    conference: Optional[str] = None,
    n: int = 10,
    ascending: Optional[bool] = None,
    qualifier: Qualifier = "qualified",
    min_pa: Optional[int] = None,
    min_ip: Optional[float] = None,
    per: Literal["season", "career"] = "season",
    include: Optional[Sequence[str]] = None,
) -> list[dict]:
    """Top N players by any statistic, sorted the right way round.

    Sort direction is chosen from the statistic unless you say otherwise, so
    ``leaderboard("era", stat_type="pitching")`` returns the best pitchers rather
    than the worst.

    Args:
        stat (str): Column name, matched case-insensitively. Counting, rate, and
            advanced statistics all work.
        stat_type (str): ``"batting"`` or ``"pitching"``.
        year (int, optional): A single season.
        years (Sequence[int], optional): Several seasons. Ignored if ``year`` is
            given.
        team (str, optional): Any spelling of a team name; resolved through the
            registry, so ``"Auburn"``, ``"AUB"`` and ``"Auburn University"`` all
            work.
        conference (str, optional): Conference code, e.g. ``"SEC"``.
        n (int): How many rows to return. Pass ``None`` for all.
        ascending (bool, optional): Force a sort direction. Defaults to whatever
            :func:`stat_direction` says.
        qualifier (str): ``"qualified"`` to restrict to players who met the
            playing-time minimum, ``"noMin"`` for everyone.
        min_pa (int, optional): Additional plate-appearance floor.
        min_ip (float, optional): Additional innings floor, in true innings.
        per (str): ``"season"`` for one row per player-season, ``"career"`` to
            aggregate a player's seasons first.
        include (Sequence[str], optional): Extra columns to carry into each row.

    Returns:
        list[dict]: Dicts with ``name``, ``team``, ``year``, ``value``, plus any
        requested extras. Empty if the statistic is unknown.

    Examples:
        >>> leaderboard("era", stat_type="pitching", year=2025, n=3)
        [{'name': 'Charlie Walker', ...}]
        >>> leaderboard("cwrc+", year=2025, conference="SEC", n=5)
    """
    df = _load_df(stat_type, qualifier)

    if per == "career":
        df = _career_frame(df, stat_type)

    colmap = {c.lower(): c for c in df.columns}
    if stat.strip().lower() not in colmap:
        return []
    column = colmap[stat.strip().lower()]

    mask = pd.Series(True, index=df.index)
    if year is not None:
        mask &= df["year"].astype(int) == int(year)
    elif years:
        mask &= df["year"].astype(int).isin([int(y) for y in years])

    if team is not None:
        team_id = as_team_id(team)
        if team_id is None:
            return []
        # Match on the acronym the player cache actually stores.
        from ncaa_bbStats.team_registry import team_aliases
        acronyms = {a.lower() for a in team_aliases(team_id, "fg_acronym")}
        mask &= df["team"].str.lower().isin(acronyms)

    if conference is not None:
        seasons = df.loc[mask, ["team", "year"]].drop_duplicates()
        keep = set()
        for _, row in seasons.iterrows():
            team_id = resolve_team(row["team"])
            if team_id and team_conference(team_id, int(row["year"])) == conference:
                keep.add((row["team"], int(row["year"])))
        mask &= [
            (t, int(y)) in keep for t, y in zip(df["team"], df["year"])
        ]

    if min_pa is not None and "pa" in df.columns:
        mask &= pd.to_numeric(df["pa"], errors="coerce").fillna(0) >= min_pa
    if min_ip is not None and "ip" in df.columns:
        true_innings = df["ip"].map(lambda v: ip_to_float(v) or 0.0)
        mask &= true_innings >= min_ip

    rows = df.loc[mask].copy()
    rows[column] = pd.to_numeric(rows[column], errors="coerce")
    rows = rows.dropna(subset=[column])
    if rows.empty:
        return []

    if ascending is None:
        ascending = stat_direction(stat, stat_type) == "lower"
    rows = rows.sort_values(by=column, ascending=ascending)
    if n is not None:
        rows = rows.head(n)

    extras = [c for c in (include or []) if c in rows.columns]
    out = []
    for _, row in rows.iterrows():
        record = {
            "name": row["name"],
            "team": row.get("team"),
            "year": int(row["year"]) if pd.notna(row.get("year")) else None,
            "value": float(row[column]),
        }
        if per == "career" and "seasons" in rows.columns:
            record["seasons"] = int(row["seasons"])
        for extra in extras:
            record[extra] = row[extra]
        out.append(record)
    return out
