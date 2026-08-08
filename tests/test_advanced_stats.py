"""Tests for the package-derived rate and run-value metrics.

The load-bearing claim is that dropping the stored rate statistics loses no
information, because every one is arithmetic on the counting stats that remain.
`test_rates_are_exactly_recoverable` is the proof: it reconstructs them from the
counting stats alone and requires an exact match against values computed
independently.
"""

import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ncaa_bbStats import advanced_stats as adv  # noqa: E402
from ncaa_bbStats._paths import data_path  # noqa: E402


# A real 2025 season: Jack Goodman, Northeastern.
BATTER = {
    "year": 2025, "g": 56, "pa": 234, "ab": 203, "h": 68, "2b": 17, "3b": 1,
    "hr": 10, "r": 51, "rbi": 48, "bb": 26, "so": 49, "hbp": 5, "sf": 0,
    "sh": 0, "gdp": 4, "sb": 9, "cs": 2,
}
# A real 2025 season: Aiven Cabral, Northeastern.
PITCHER = {
    "year": 2025, "w": 8, "l": 3, "g": 15, "gs": 15, "cg": 1, "sho": 0, "sv": 0,
    "ip": 89.1, "tbf": 361, "h": 63, "r": 34, "er": 29, "hr": 6, "bb": 29,
    "hbp": 6, "wp": 3, "bk": 0, "so": 74,
}


def test_ip_to_float_reads_ncaa_thirds():
    """NCAA writes thirds as tenths; a decimal read understates outs."""
    assert adv.ip_to_float(97.0) == 97.0
    assert adv.ip_to_float(97.1) == pytest.approx(97 + 1 / 3)
    assert adv.ip_to_float(97.2) == pytest.approx(97 + 2 / 3)
    assert adv.ip_to_float(None) is None
    assert adv.ip_to_float("nonsense") is None


def test_rates_are_exactly_recoverable():
    """Every dropped rate statistic is reproduced from the counting stats.

    This is why the cache stores counting stats only.
    """
    import pandas as pd

    df = pd.DataFrame([BATTER])
    out = adv.add_advanced_columns(df, "batting").iloc[0]

    singles = BATTER["h"] - BATTER["2b"] - BATTER["3b"] - BATTER["hr"]
    tb = singles + 2 * BATTER["2b"] + 3 * BATTER["3b"] + 4 * BATTER["hr"]
    woba_pa = BATTER["ab"] + BATTER["bb"] + BATTER["hbp"] + BATTER["sf"]

    assert out["avg"] == pytest.approx(BATTER["h"] / BATTER["ab"])
    assert out["obp"] == pytest.approx(
        (BATTER["h"] + BATTER["bb"] + BATTER["hbp"]) / woba_pa
    )
    assert out["slg"] == pytest.approx(tb / BATTER["ab"])
    assert out["ops"] == pytest.approx(out["obp"] + out["slg"])
    assert out["iso"] == pytest.approx(out["slg"] - out["avg"])

    pdf = pd.DataFrame([PITCHER])
    pout = adv.add_advanced_columns(pdf, "pitching").iloc[0]
    innings = adv.ip_to_float(PITCHER["ip"])
    assert pout["era"] == pytest.approx(9 * PITCHER["er"] / innings)
    assert pout["whip"] == pytest.approx((PITCHER["bb"] + PITCHER["h"]) / innings)
    assert pout["k/9"] == pytest.approx(9 * PITCHER["so"] / innings)


def test_cwoba_is_scaled_to_league_obp():
    """cwOBA's whole point is landing on the OBP scale, so a good hitter is ~.400."""
    value = adv.cwoba(BATTER, 2025, 1)
    constants = adv.league_constants(2025, 1, "batting")
    assert 0.25 < value < 0.65
    # This batter is above average, so above the league mark.
    assert value > constants["lg_cwoba"]


def test_cwrc_plus_is_centred_on_100():
    """A league-average line must index at exactly 100."""
    constants = adv.league_constants(2025, 1, "batting")

    # Construct a line whose cwOBA is the league mark by scaling a real one.
    assert adv.cwrc_plus(BATTER, 2025, 1) > 100  # above-average hitter

    weak = dict(BATTER, h=30, **{"2b": 4, "3b": 0, "hr": 1}, bb=5, hbp=0)
    assert adv.cwrc_plus(weak, 2025, 1) < 100

    league_average_ish = adv.cwrc_plus(
        {"year": 2025, "ab": 1000, "h": 0, "2b": 0, "3b": 0, "hr": 0,
         "bb": 0, "hbp": 0, "sf": 0, "pa": 1000, "so": 0}, 2025, 1
    )
    # A line that never reaches base is worth roughly nothing, not 100.
    assert league_average_ish < 20


def test_cfip_is_on_the_era_scale():
    """cFIP should sit near, but not equal, the pitcher's ERA."""
    cfip = adv.cfip(PITCHER, 2025, 1)
    era = 9 * PITCHER["er"] / adv.ip_to_float(PITCHER["ip"])
    assert 1.0 < cfip < 12.0
    assert abs(cfip - era) < 4.0


def test_clob_pct_is_a_proportion():
    value = adv.clob_pct(PITCHER)
    assert 0.0 < value < 1.0


def test_cspd_is_bounded():
    value = adv.cspd(BATTER)
    assert 0.0 <= value <= 10.0


def test_metrics_return_none_before_constants_exist():
    """Seasons too sparse to fit weights must return None, not a fabricated value.

    2002-2007 record only at-bats, hits and runs.
    """
    for year in (2002, 2005, 2007):
        assert adv.cwoba(dict(BATTER, year=year), year, 1) is None
        assert adv.cwrc_plus(dict(BATTER, year=year), year, 1) is None
        assert adv.cfip(dict(PITCHER, year=year), year, 1) is None
        assert adv.league_constants(year, 1) is None


def test_metrics_return_none_on_missing_inputs():
    assert adv.cwoba({"year": 2025}, 2025, 1) is None
    assert adv.cfip({"year": 2025}, 2025, 1) is None
    assert adv.clob_pct({}) is None


def test_constants_cover_the_expected_seasons():
    """Weights begin once a division reports the full batting event set.

    2002-2007 record only at-bats, hits and runs everywhere. Division III also
    has a gap at 2011, when it stopped reporting walks, hit-by-pitch and
    sacrifice flies -- that season is skipped rather than fitted on partial data.
    """
    for division in (1, 2, 3):
        seasons = adv.seasons_with_constants(division)
        assert seasons[0] >= 2008, f"division {division} starts at {seasons[0]}"
        assert seasons[-1] == 2026
        assert not set(seasons) & set(range(2002, 2008))

    assert 2011 not in adv.seasons_with_constants(3)


@pytest.mark.parametrize("division", [1, 2, 3])
def test_run_values_obey_the_ordering_physics_requires(division):
    """A home run cannot be worth less than a triple, and so on down the chain.

    The unconstrained fit violates this in 34 of 55 division-seasons, because
    triples are rare enough that their coefficient absorbs rally context.
    tools/build_league_constants.enforce_monotone_hits projects it back.
    """
    for year in adv.seasons_with_constants(division):
        c = adv.league_constants(year, division, "batting")
        assert c["w_1b"] <= c["w_2b"] <= c["w_3b"] <= c["w_hr"], (
            f"run values out of order for division {division} {year}"
        )
        assert c["w_bb"] < c["w_1b"], "a walk cannot beat a single"
        assert c["w_cs"] < 0 < c["w_sb"], "caught stealing must cost runs"
        assert c["park_factor"] == 1.0


@pytest.mark.parametrize("division", [1, 2, 3])
def test_fit_quality_is_reasonable(division):
    """Guards against a silently degenerate fit."""
    for year in adv.seasons_with_constants(division):
        c = adv.league_constants(year, division, "batting")
        assert c["r2"] > 0.85, f"division {division} {year} R2 = {c['r2']}"
        assert 0 < c["lg_obp"] < 0.5
        assert 0 < c["lg_r_pa"] < 0.3
        assert c["n_teams"] >= 60


def test_league_constants_regenerate_identically(tmp_path):
    """The constants are a pure function of the public team-stats cache.

    If this fails, either the cache changed (expected -- rerun the builder and
    commit) or the builder is not deterministic (not expected).
    """
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "build_league_constants.py"),
         "--out", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr[-2000:]

    for name in ("batting_weights.csv", "pitching_constants.csv"):
        committed = pathlib.Path(data_path("league_constants", name)).read_bytes()
        regenerated = (tmp_path / name).read_bytes()
        assert committed == regenerated, (
            f"{name} differs from a fresh build. Rerun "
            "tools/build_league_constants.py and commit the result."
        )


def test_league_constants_is_cached():
    """`add_advanced_columns` calls this once per row per metric.

    Uncached, the boolean filter it performs dominated package load time --
    ~294k calls resolving to 10 distinct keys, which cost 21s to build the
    batting frame and 0.4s once cached. A web app pays that on every cold
    start, so the cache is load-bearing rather than an optimisation.
    """
    adv._lookup_constants.cache_clear()
    before = adv._lookup_constants.cache_info()
    for _ in range(50):
        adv.league_constants(2025, 1, "batting")
    after = adv._lookup_constants.cache_info()

    assert after.misses - before.misses == 1, "each key should be looked up once"
    assert after.hits - before.hits == 49


def test_league_constants_result_is_not_shared():
    """A caller mutating the returned dict must not corrupt the cache."""
    first = adv.league_constants(2025, 1, "batting")
    original = first["w_hr"]
    first["w_hr"] = 999.0

    assert adv.league_constants(2025, 1, "batting")["w_hr"] == original


@pytest.mark.parametrize("year", [None, float("nan"), "not-a-year"])
def test_league_constants_rejects_unusable_years(year):
    """A missing year reaches this function from rows with no season."""
    assert adv.league_constants(year, 1, "batting") is None
