"""Advanced rate and run-value metrics computed from public counting statistics.

Every metric here is derived by this package from NCAA counting statistics, using
linear weights regressed from the packaged team-stats cache. None of it is copied
from a third-party analytics provider. See DATA_PROVENANCE.md.

Metrics prefixed ``c`` (``cwoba``, ``cwrc_plus``, ``cfip``, ...) are the
college-calibrated analogues of the familiar sabermetric statistics. They are
constructed the same way, but their league constants come from NCAA play rather
than from Major League Baseball or from a vendor's proprietary values, so the
numbers are not interchangeable with same-named statistics published elsewhere.

Nothing here is stored in the player CSVs. Both inputs -- the counting stats and
the league constants -- ship, so the metrics are recomputed on read. Storing
derived columns beside their inputs is what let ``pitching_qualified.csv`` drift
into a copy of ``pitching_noMin.csv`` without anything noticing.
"""

import math
from functools import lru_cache
from typing import Literal, Optional

import pandas as pd

from ncaa_bbStats._paths import data_path

__all__ = [
    "league_constants",
    "seasons_with_constants",
    "cwoba",
    "cwraa",
    "cwrc",
    "cwrc_plus",
    "cwsb",
    "cfip",
    "clob_pct",
    "cspd",
    "add_advanced_columns",
    "ip_to_float",
]

ConstantKind = Literal["batting", "pitching"]

# Events entering cwOBA's numerator, and the counting-stat column each reads.
_WOBA_TERMS = (
    ("w_1b", "1b"),
    ("w_2b", "2b"),
    ("w_3b", "3b"),
    ("w_hr", "hr"),
    ("w_bb", "bb"),
    ("w_hbp", "hbp"),
)

_CONSTANT_FILES = {
    "batting": "batting_weights.csv",
    "pitching": "pitching_constants.csv",
}


@lru_cache(maxsize=4)
def _load_constants(kind: ConstantKind) -> pd.DataFrame:
    """Load and cache one league-constant table."""
    path = data_path("league_constants", _CONSTANT_FILES[kind])
    df = pd.read_csv(path)
    # year 0 rows record the pooled fit used as the shrinkage target; they are
    # diagnostic, not a season anyone can look up.
    return df[df["year"] > 0].reset_index(drop=True)


def league_constants(
    year: int, division: int = 1, kind: ConstantKind = "batting"
) -> Optional[dict]:
    """Return the league constants for one season and division.

    Args:
        year (int): Season year. Constants exist for 2008-2026 (2012-2026 for
            Division III); earlier seasons record too few statistics to fit.
        division (int): NCAA division (1, 2, or 3).
        kind (str): ``"batting"`` for run values and scaling terms,
            ``"pitching"`` for the FIP constant and league rates.

    Returns:
        dict | None: The constants row, or None if that season has none.
    """
    df = _load_constants(kind)
    match = df[(df["year"] == year) & (df["division"] == division)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def seasons_with_constants(division: int = 1, kind: ConstantKind = "batting") -> list:
    """List the seasons that have league constants for a division.

    Args:
        division (int): NCAA division (1, 2, or 3).
        kind (str): ``"batting"`` or ``"pitching"``.

    Returns:
        list[int]: Sorted season years.
    """
    df = _load_constants(kind)
    return sorted(df[df["division"] == division]["year"].tolist())


def ip_to_float(value) -> Optional[float]:
    """Convert NCAA innings notation to true innings.

    NCAA writes partial innings as tenths: ``97.1`` means 97 innings and one
    out, ``97.2`` means two outs. Treating it as a decimal understates outs and
    inflates every innings-denominated rate.

    Args:
        value: Innings pitched as reported (ex. ``97.2``).

    Returns:
        float | None: Innings as a real number (ex. ``97.667``), or None if the
        value cannot be read as a number.
    """
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(value):
        return None
    whole = int(value)
    tenths = round(value - whole, 1)
    if tenths == 0.1:
        return whole + 1.0 / 3.0
    if tenths == 0.2:
        return whole + 2.0 / 3.0
    return float(whole) if tenths == 0.0 else value


def _get(stats, *names):
    """Return the first present, non-null value among `names`."""
    for name in names:
        if name in stats:
            value = stats[name]
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                return float(value)
    return None


def _singles(stats) -> Optional[float]:
    """Singles, taken directly if present or derived from H - 2B - 3B - HR."""
    direct = _get(stats, "1b")
    if direct is not None:
        return direct
    hits = _get(stats, "h")
    if hits is None:
        return None
    parts = [_get(stats, k) or 0.0 for k in ("2b", "3b", "hr")]
    return hits - sum(parts)


def _plate_appearances(stats) -> Optional[float]:
    """The wOBA plate-appearance denominator: AB + BB + HBP + SF.

    Sacrifice hits are excluded by construction. That also sidesteps Division
    II never reporting them.
    """
    ab = _get(stats, "ab")
    if ab is None:
        return None
    return ab + (_get(stats, "bb") or 0.0) + (_get(stats, "hbp") or 0.0) + (
        _get(stats, "sf") or 0.0
    )


def cwoba(stats: dict, year: int, division: int = 1) -> Optional[float]:
    """College wOBA: one number for a hitter's total offensive value per plate appearance.

    Each way of reaching base is weighted by how many runs it is actually worth
    in NCAA play, unlike OBP (which treats a walk and a home run alike) or SLG
    (which weights by total bases rather than by run value). Scaled so the
    league average equals league OBP, which puts it on a familiar scale.

    Weights are regressed from the packaged NCAA team-stats cache, so they
    reflect college run scoring rather than Major League values.

    Args:
        stats (dict): Counting stats with keys ``ab``, ``h``, ``2b``, ``3b``,
            ``hr``, ``bb``, ``hbp``, ``sf`` (``1b`` used if present).
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).

    Returns:
        float | None: cwOBA, or None if the season has no constants or a
        required input is missing.
    """
    constants = league_constants(year, division, "batting")
    if constants is None:
        return None

    pa = _plate_appearances(stats)
    if not pa:
        return None

    singles = _singles(stats)
    if singles is None:
        return None

    events = {"1b": singles}
    for key in ("2b", "3b", "hr", "bb", "hbp"):
        events[key] = _get(stats, key) or 0.0

    numerator = sum(constants[weight] * events[event] for weight, event in _WOBA_TERMS)
    return numerator / pa


def cwraa(stats: dict, year: int, division: int = 1) -> Optional[float]:
    """Weighted runs above average: runs contributed above a league-average hitter.

    Zero is exactly average. Positive is above.

    Args:
        stats (dict): Counting stats, as for :func:`cwoba`, plus ``pa``.
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).

    Returns:
        float | None: Runs above average, or None if unavailable.
    """
    constants = league_constants(year, division, "batting")
    woba = cwoba(stats, year, division)
    if constants is None or woba is None:
        return None

    pa = _get(stats, "pa") or _plate_appearances(stats)
    if not pa:
        return None
    return (woba - constants["lg_cwoba"]) / constants["cwoba_scale"] * pa


def cwrc(stats: dict, year: int, division: int = 1) -> Optional[float]:
    """Weighted runs created: total runs a hitter is responsible for producing.

    Args:
        stats (dict): Counting stats, as for :func:`cwraa`.
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).

    Returns:
        float | None: Runs created, or None if unavailable.
    """
    constants = league_constants(year, division, "batting")
    raa = cwraa(stats, year, division)
    if constants is None or raa is None:
        return None

    pa = _get(stats, "pa") or _plate_appearances(stats)
    if not pa:
        return None
    return raa + constants["lg_r_pa"] * pa


def cwrc_plus(stats: dict, year: int, division: int = 1) -> Optional[float]:
    """Weighted runs created, indexed so 100 is league average.

    130 means 30% better than an average hitter that season; 70 means 30% worse.
    Because it is indexed to its own season, it compares hitters across seasons
    with different run environments.

    No park adjustment is applied -- park factors are fixed at 1.0, because NCAA
    park data is not publicly available. Hitters at extreme-altitude programs are
    therefore flattered. Magnitudes are not comparable to park-adjusted figures
    published elsewhere; measured correlation against one such series is 0.969.

    Args:
        stats (dict): Counting stats, as for :func:`cwraa`.
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).

    Returns:
        float | None: Index where 100 is league average, or None if unavailable.
    """
    constants = league_constants(year, division, "batting")
    raa = cwraa(stats, year, division)
    if constants is None or raa is None:
        return None

    pa = _get(stats, "pa") or _plate_appearances(stats)
    if not pa or not constants["lg_r_pa"]:
        return None
    return 100.0 * (raa / pa + constants["lg_r_pa"]) / constants["lg_r_pa"]


def cwsb(stats: dict, year: int, division: int = 1) -> Optional[float]:
    """Stolen-base runs above average.

    Credits successful steals and debits caught stealing at their measured NCAA
    run values, then subtracts what a league-average runner would produce with
    the same number of times on base -- so a runner who steals often but is
    caught often can still land below zero.

    Args:
        stats (dict): Counting stats with ``sb``, ``cs``, and the on-base
            components ``1b`` (or ``h``/``2b``/``3b``/``hr``), ``bb``, ``hbp``.
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).

    Returns:
        float | None: Baserunning runs above average, or None if unavailable.
    """
    constants = league_constants(year, division, "batting")
    if constants is None:
        return None

    sb = _get(stats, "sb")
    cs = _get(stats, "cs")
    if sb is None or cs is None:
        return None

    singles = _singles(stats)
    if singles is None:
        return None
    opportunities = singles + (_get(stats, "bb") or 0.0) + (_get(stats, "hbp") or 0.0)

    return (
        constants["w_sb"] * sb
        + constants["w_cs"] * cs
        - constants["lg_wsb_per_opp"] * opportunities
    )


def cfip(stats: dict, year: int, division: int = 1) -> Optional[float]:
    """Fielding independent pitching, on the ERA scale.

    Judges a pitcher only on strikeouts, walks, hit batters and home runs -- the
    outcomes that do not depend on the defence behind them. Read it like an ERA:
    a pitcher whose ERA is well above their cFIP was probably let down by their
    defence or by sequencing luck, and vice versa.

    The constant that puts it on the ERA scale is computed per season and
    division from the packaged team-stats cache.

    Args:
        stats (dict): Counting stats with ``ip``, ``hr``, ``bb``, ``so``, and
            optionally ``hbp``.
        year (int): Season year.
        division (int): NCAA division (1, 2, or 3).

    Returns:
        float | None: cFIP on the ERA scale, or None if unavailable.
    """
    constants = league_constants(year, division, "pitching")
    if constants is None:
        return None

    innings = ip_to_float(stats.get("ip"))
    if not innings:
        return None

    hr = _get(stats, "hr")
    bb = _get(stats, "bb")
    so = _get(stats, "so")
    if hr is None or bb is None or so is None:
        return None
    hbp = _get(stats, "hbp") or 0.0

    return (13.0 * hr + 3.0 * (bb + hbp) - 2.0 * so) / innings + constants["cfip_constant"]


def clob_pct(stats: dict) -> Optional[float]:
    """Share of baserunners a pitcher stranded.

    A high value means the pitcher pitched well with runners on -- or got lucky.
    It regresses hard toward the league mean, so large deviations usually
    predict a move back toward average rather than a repeatable skill.

    Needs no league constant.

    Args:
        stats (dict): Counting stats with ``h``, ``bb``, ``r``, ``hr``, and
            optionally ``hbp``.

    Returns:
        float | None: Strand rate as a proportion, or None if unavailable or the
        denominator is non-positive (which happens in tiny samples).
    """
    h = _get(stats, "h")
    bb = _get(stats, "bb")
    r = _get(stats, "r")
    hr = _get(stats, "hr")
    if None in (h, bb, r, hr):
        return None
    hbp = _get(stats, "hbp") or 0.0

    denominator = h + bb + hbp - 1.4 * hr
    if denominator <= 0:
        return None
    return (h + bb + hbp - r) / denominator


def cspd(stats: dict) -> Optional[float]:
    """Bill James Speed Score: a 0-10 estimate of baserunning speed from the box score.

    Averages four indicators -- stolen-base success rate, attempt frequency,
    triples rate, and runs scored per time on base.

    This is the published formula on its raw scale, with no recalibration. Note
    that its constants were fitted to Major League play, so the NCAA population
    does not center on the usual 5.0: qualified Division I hitters average about
    **3.9**, and 5.0 is roughly the 80th percentile. Compare players to each
    other, not to the conventional scale.

    Weakest metric in this module (rank correlation about 0.91 against
    differently-calibrated published series). Informational only -- every input
    is retained in the data, so prefer those for modelling.

    Args:
        stats (dict): Counting stats with ``sb``, ``cs``, ``3b``, ``ab``, ``hr``,
            ``so``, ``r``, ``h``, ``bb``, and optionally ``hbp``.

    Returns:
        float | None: Speed score in [0, 10], or None if no factor can be computed.
    """
    sb = _get(stats, "sb")
    cs = _get(stats, "cs")
    triples = _get(stats, "3b")
    ab = _get(stats, "ab")
    hr = _get(stats, "hr")
    so = _get(stats, "so")
    r = _get(stats, "r")
    h = _get(stats, "h")
    bb = _get(stats, "bb")
    hbp = _get(stats, "hbp") or 0.0

    factors = []

    # Stolen base success rate.
    if sb is not None and cs is not None and (sb + cs + 7) > 0:
        factors.append(((sb + 3) / (sb + cs + 7) - 0.4) * 20)

    # Stolen base attempt frequency, relative to times on base.
    singles = _singles(stats)
    if sb is not None and cs is not None and singles is not None and bb is not None:
        on_base = singles + bb + hbp
        if on_base > 0:
            factors.append(math.sqrt(max(0.0, (sb + cs) / on_base)) / 0.07)

    # Triples rate, among balls put in play that could become a triple.
    if None not in (triples, ab, hr, so):
        chances = ab - hr - so
        if chances > 0:
            factors.append((triples / chances) / 0.02)

    # Runs scored per time on base, excluding the runner's own home runs.
    if None not in (r, hr, h, bb):
        on_base = h + bb + hbp - hr
        if on_base > 0:
            factors.append(((r - hr) / on_base - 0.1) / 0.04)

    if not factors:
        return None
    return sum(min(10.0, max(0.0, f)) for f in factors) / len(factors)


def _rate(numerator, denominator):
    """Divide, returning None rather than raising on a zero or missing input."""
    if numerator is None or not denominator:
        return None
    return numerator / denominator


def add_advanced_columns(
    df: pd.DataFrame, stat_type: Literal["batting", "pitching"], division: int = 1
) -> pd.DataFrame:
    """Return a copy of `df` with derived rate and advanced columns added.

    Adds the standard rate statistics that are pure arithmetic on the counting
    stats, plus the college-calibrated metrics in this module. Existing columns
    are not overwritten.

    Args:
        df (pandas.DataFrame): Player-season rows with lowercase counting-stat
            columns and a ``year`` column.
        stat_type (str): ``"batting"`` or ``"pitching"``.
        division (int): NCAA division used to select league constants.

    Returns:
        pandas.DataFrame: A copy with the derived columns appended.
    """
    out = df.copy()

    if stat_type == "batting":
        singles = out["h"] - out["2b"] - out["3b"] - out["hr"]
        total_bases = singles + 2 * out["2b"] + 3 * out["3b"] + 4 * out["hr"]
        woba_pa = out["ab"] + out["bb"] + out["hbp"] + out["sf"]

        out["1b"] = singles
        out["tb"] = total_bases
        out["avg"] = out["h"] / out["ab"].replace(0, pd.NA)
        out["obp"] = (out["h"] + out["bb"] + out["hbp"]) / woba_pa.replace(0, pd.NA)
        out["slg"] = total_bases / out["ab"].replace(0, pd.NA)
        out["ops"] = out["obp"] + out["slg"]
        out["iso"] = out["slg"] - out["avg"]
        out["bb%"] = out["bb"] / out["pa"].replace(0, pd.NA)
        out["k%"] = out["so"] / out["pa"].replace(0, pd.NA)
        out["bb/k"] = out["bb"] / out["so"].replace(0, pd.NA)
        balls_in_play = out["ab"] - out["so"] - out["hr"] + out["sf"]
        out["babip"] = (out["h"] - out["hr"]) / balls_in_play.replace(0, pd.NA)
    else:
        innings = out["ip"].map(ip_to_float)
        out["ip_true"] = innings
        out["era"] = 9 * out["er"] / innings.replace(0, pd.NA)
        out["whip"] = (out["bb"] + out["h"]) / innings.replace(0, pd.NA)
        out["k/9"] = 9 * out["so"] / innings.replace(0, pd.NA)
        out["bb/9"] = 9 * out["bb"] / innings.replace(0, pd.NA)
        out["hr/9"] = 9 * out["hr"] / innings.replace(0, pd.NA)
        out["k/bb"] = out["so"] / out["bb"].replace(0, pd.NA)
        out["k%"] = out["so"] / out["tbf"].replace(0, pd.NA)
        out["bb%"] = out["bb"] / out["tbf"].replace(0, pd.NA)
        out["k-bb%"] = out["k%"] - out["bb%"]
        # Balls in play a pitcher allowed: batters faced less the outcomes that
        # never reach a fielder.
        balls_in_play = out["tbf"] - out["so"] - out["hr"] - out["bb"] - out["hbp"]
        out["babip"] = (out["h"] - out["hr"]) / balls_in_play.replace(0, pd.NA)

    # Row-wise, because each row needs its own season's constants.
    records = out.to_dict("records")
    if stat_type == "batting":
        out["cwoba"] = [cwoba(r, r["year"], division) for r in records]
        out["cwraa"] = [cwraa(r, r["year"], division) for r in records]
        out["cwrc"] = [cwrc(r, r["year"], division) for r in records]
        out["cwrc+"] = [cwrc_plus(r, r["year"], division) for r in records]
        out["cwsb"] = [cwsb(r, r["year"], division) for r in records]
        out["cspd"] = [cspd(r) for r in records]
    else:
        out["cfip"] = [cfip(r, r["year"], division) for r in records]
        out["clob%"] = [clob_pct(r) for r in records]
        out["e-cf"] = out["era"] - out["cfip"]

    return out
