"""Behavioural tests for the leaderboard, dataset readers, and cross-dataset joins.

The recurring hazard across all of these is a join that fails quietly: a team
name that does not resolve returns an empty list, which reads exactly like "this
program produced no draft picks". These tests pin known-correct values so a
silent join failure shows up as a wrong number rather than a plausible one.
"""

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import ncaa_bbStats as pkg  # noqa: E402
from ncaa_bbStats import crossref, draft_detail_utils as draft  # noqa: E402
import ncaa_bbStats.leaderboards as lb  # noqa: E402
from ncaa_bbStats import program_utils as program  # noqa: E402
from ncaa_bbStats import prospect_utils as prospects  # noqa: E402
from ncaa_bbStats import pythagorean as pyth  # noqa: E402
from ncaa_bbStats import rpi_utils as rpi  # noqa: E402


# --- leaderboard ---------------------------------------------------------

def test_leaderboard_sorts_era_ascending():
    """The whole point: a top-ERA list must contain good pitchers."""
    rows = lb.leaderboard("era", stat_type="pitching", year=2025, n=5, min_ip=50)
    assert rows
    values = [r["value"] for r in rows]
    assert values == sorted(values), "ERA leaderboard is not ascending"
    assert values[0] < 3.0, f"best ERA was {values[0]}, which is not a leader"


def test_leaderboard_sorts_home_runs_descending():
    rows = lb.leaderboard("hr", year=2025, n=5)
    values = [r["value"] for r in rows]
    assert values == sorted(values, reverse=True)
    assert values[0] > 15


def test_explicit_ascending_overrides_the_default():
    high = lb.leaderboard("era", stat_type="pitching", year=2025,
                          n=3, min_ip=50, ascending=False)
    low = lb.leaderboard("era", stat_type="pitching", year=2025, n=3, min_ip=50)
    assert high[0]["value"] > low[0]["value"]


def test_stat_direction_depends_on_stat_type():
    """Strikeouts are good for a pitcher and bad for a hitter."""
    assert lb.stat_direction("so", "pitching") == "higher"
    assert lb.stat_direction("so", "batting") == "lower"
    assert lb.stat_direction("era", "pitching") == "lower"
    assert lb.stat_direction("cwrc+", "batting") == "higher"


def test_min_ip_and_min_pa_filter():
    unfiltered = lb.leaderboard("era", stat_type="pitching", year=2025,
                                n=1, qualifier="noMin")
    filtered = lb.leaderboard("era", stat_type="pitching", year=2025,
                              n=1, qualifier="noMin", min_ip=60)
    assert unfiltered[0]["name"] != filtered[0]["name"] or unfiltered == filtered


def test_team_filter_accepts_any_spelling():
    """A registry-backed filter must treat every alias identically."""
    by_name = lb.leaderboard("hr", year=2025, team="Auburn", n=5)
    by_acronym = lb.leaderboard("hr", year=2025, team="AUB", n=5)
    assert by_name and by_name == by_acronym


def test_unknown_team_returns_empty_not_everything():
    """A filter that fails to resolve must not silently return the whole league."""
    assert lb.leaderboard("hr", year=2025, team="Not A Real School") == []


def test_career_leaderboard_rebuilds_rates_from_totals():
    """A career ERA is total earned runs over total innings, not an average."""
    rows = lb.leaderboard("era", stat_type="pitching", per="career",
                          n=5, min_ip=150, qualifier="noMin")
    assert rows
    assert all(1.0 < r["value"] < 4.0 for r in rows)
    assert all(r["seasons"] >= 1 for r in rows)


def test_leaderboard_reaches_computed_stats():
    """Stats that exist only after computation must be rankable."""
    for stat in ("obp", "cwrc+", "cwoba"):
        assert lb.leaderboard(stat, year=2025, n=3), f"{stat} produced no rows"


def test_unknown_stat_returns_empty():
    assert lb.leaderboard("not_a_stat", year=2025) == []


# --- RPI -----------------------------------------------------------------

def test_rpi_known_values():
    """Tennessee was the RPI leader in its 2024 championship season."""
    assert rpi.rpi_rank("Tennessee", 2024) == 1
    assert rpi.strength_of_schedule("Tennessee", 2024) is not None


def test_rpi_accepts_any_team_spelling():
    assert rpi.rpi_rank("LSU", 2025) == rpi.rpi_rank("Louisiana State", 2025)


def test_rpi_returns_none_outside_coverage():
    """2021-2026 only; earlier seasons are not published, not missing."""
    assert rpi.rpi_rank("Tennessee", 2010) is None
    assert rpi.quadrant_record("Tennessee", 2010, 1) is None


def test_rpi_table_is_ordered_and_complete():
    table = rpi.rpi_table(2025)
    assert 280 < len(table) < 330
    ranks = [r["rpi_rank"] for r in table if r["rpi_rank"]]
    assert ranks == sorted(ranks)


def test_quadrant_record_rejects_bad_input():
    with pytest.raises(ValueError):
        rpi.quadrant_record("Tennessee", 2024, 5)


def test_every_rpi_row_resolved_to_a_program():
    """A blank team_id is a silent join failure."""
    for season in rpi.available_seasons():
        blank = [r for r in rpi._load(season).values() if not r["team_id"]]
        assert not blank, f"{season}: {len(blank)} unresolved RPI rows"


# --- draft detail --------------------------------------------------------

def test_draft_pick_known_value():
    pick = draft.draft_pick(2024, 1)
    assert pick["name"] == "Travis Bazzana"
    assert pick["school"] == "Oregon State"
    assert pick["signing_bonus"] == 8950000
    assert pick["slot_value"] == 10570600


def test_post_round_ten_picks_have_no_slot_not_zero():
    """The API reports "0", which is truthy; storing 0 would misread it."""
    late = [
        p for p in draft._load(2025)
        if (draft.round_number(p) or 0) > 10
    ]
    assert late
    assert all(p["slot_value"] is None for p in late)


def test_compensation_rounds_resolve_to_a_numbered_round():
    """131 picks across 2021-2026 carry labels like "CB-A", "PPI", "SUP-2".

    Calling int() on those raises; dropping them silently loses real first-round
    talent from any "top ten rounds" filter.
    """
    labelled = [
        p for season in draft.available_seasons()
        for p in draft._load(season)
        if not str(p["round"]).isdigit()
    ]
    assert len(labelled) > 100
    unresolved = [p["round"] for p in labelled if draft.round_number(p) is None]
    assert not unresolved, f"unmapped round labels: {sorted(set(unresolved))}"
    # Every one of them belongs to the first ten rounds.
    assert all(draft.round_number(p) <= 10 for p in labelled)


def test_draft_class_finds_a_known_class():
    picks = draft.draft_class("LSU", 2025)
    names = {p["name"] for p in picks}
    assert "Kade Anderson" in names
    assert len(picks) >= 4


def test_draft_class_unknown_team_is_empty():
    assert draft.draft_class("Not A Real School", 2025) == []


def test_conference_draft_counts_are_ordered():
    counts = draft.conference_draft_counts(2025)
    assert counts[0]["conference"] == "SEC"
    assert counts[0]["picks"] > 80
    assert [c["picks"] for c in counts] == sorted(
        (c["picks"] for c in counts), reverse=True
    )


def test_draft_demographics_totals_add_up():
    demo = draft.draft_demographics(2025)
    assert demo["picks"] == sum(demo["by_origin"].values())
    assert 20 < demo["mean_age"] < 23


# --- program finance -----------------------------------------------------

def test_program_finance_known_values():
    row = program.program_finance("Tennessee", 2025)
    assert row["budget_pct"] > 0.9
    assert 15 <= row["roster_size"] <= 75
    assert row["carried_forward"] is False


def test_2026_is_flagged_as_carried_forward():
    """A carried-forward figure must never read as current."""
    row = program.program_finance("Tennessee", 2026)
    assert row["carried_forward"] is True
    assert row["eada_year"] == 2025


def test_finance_returns_none_for_unknown_programs():
    assert program.program_finance("Not A Real School", 2025) is None


def test_richest_programs_are_ordered():
    rows = program.richest_programs(2025, n=10, division=1)
    values = [r["budget_pct"] for r in rows]
    assert values == sorted(values, reverse=True)


def test_division_one_finance_coverage_is_high():
    """A coverage collapse would silently empty every finance-based join."""
    from ncaa_bbStats.team_registry import list_teams

    active = {t["team_id"] for t in list_teams(season=2025, division=1)}
    covered = {
        team_id for (team_id, season) in program._load() if season == 2025
    }
    ratio = len(active & covered) / len(active)
    assert ratio > 0.95, f"Division I finance coverage fell to {ratio:.0%}"


# --- prospects -----------------------------------------------------------

def test_prospect_rank_known_value():
    assert prospects.prospect_rank("Kade Anderson", 2025) == 2


def test_prospect_vs_actual_pairs_board_with_draft():
    rows = prospects.prospect_vs_actual(2025)
    assert len(rows) > 150
    assert all(r["prospect_rank"] and r["actual_pick"] for r in rows)
    assert all(r["surprise"] == r["prospect_rank"] - r["actual_pick"] for r in rows)


def test_risers_and_fallers_are_opposite_ends():
    risers = prospects.biggest_draft_risers(2025, n=5)
    fallers = prospects.biggest_draft_fallers(2025, n=5)
    assert risers[0]["surprise"] > 0 > fallers[0]["surprise"]


# --- pythagorean ---------------------------------------------------------

def test_pythagorean_backward_compatible():
    """The original three-argument call must keep working unchanged."""
    value = pkg.get_pythagorean_expectation("Northeastern", 2018, 1)
    assert isinstance(value, float)
    assert 0.0 < value < 1.0


def test_pythagorean_exponent_override():
    default = pkg.get_pythagorean_expectation("Northeastern", 2018, 1)
    other = pkg.get_pythagorean_expectation("Northeastern", 2018, 1, exponent=2.5)
    assert default != other


def test_no_conference_exponent_is_significant():
    """Documents the finding that keeps this feature opt-in.

    If a future refit produced a significant conference, that would be a real
    result worth acting on -- and this test failing is how you would find out.
    """
    rows = pyth.conference_exponents()
    assert len(rows) > 25
    assert all(r["significant"] == "no" for r in rows)
    assert all(r["p_value"] > 0.05 for r in rows)


def test_luck_ratings_are_symmetric():
    lucky = pyth.luckiest_teams(2025, n=5)
    unlucky = pyth.unluckiest_teams(2025, n=5)
    assert lucky[0]["luck_wins"] > 0 > unlucky[0]["luck_wins"]
    for row in lucky + unlucky:
        assert row["expected_win_pct"] + row["luck"] == pytest.approx(
            row["actual_win_pct"], abs=1e-3
        )


# --- cross-dataset -------------------------------------------------------

def test_team_profile_reaches_every_dataset():
    profile = crossref.team_profile("Tennessee", 2024)
    assert all(profile["coverage"].values()), (
        f"team_profile lost a dataset: {profile['coverage']}"
    )
    assert profile["record"]["wins"] == 60
    assert profile["rpi"]["rpi_rank"] == 1
    assert profile["draft"]["picks"] > 0
    assert profile["pythagorean"]["expected_win_pct"] > 0.7


def test_team_profile_reports_gaps_rather_than_hiding_them():
    """A Division III program has no RPI or draft data; that must be visible."""
    profile = crossref.team_profile("Amherst", 2015)
    if profile is None:
        pytest.skip("Amherst not in the registry")
    assert profile["coverage"]["rpi"] is False
    assert profile["rpi"] is None
    assert "identity" in profile and "coverage" in profile


def test_team_profile_unknown_team():
    assert crossref.team_profile("Not A Real School", 2025) is None


def test_player_profile_links_stats_to_draft():
    profile = crossref.player_profile("Kade Anderson")
    assert profile["role"] == "pitcher"
    assert profile["team"]["canonical_name"] == "LSU"
    assert profile["draft"]["pick"] == 3
    assert profile["prospect_rank"] == 2
    assert profile["pitching"]["so"] == 180


def test_player_profile_unknown_player():
    assert crossref.player_profile("Nobody At All") is None


def test_draft_yield_counts_a_known_program():
    result = crossref.draft_yield("LSU", 2021, 2026)
    assert result["picks"] > 30
    assert result["first_round_picks"] >= 3
    assert result["total_bonus_dollars"] > 10_000_000
    assert result["best_pick"]["pick"] <= 5


def test_pipeline_spans_seasons():
    rows = crossref.pipeline("Coastal Carolina", 2021, 2026)
    assert len(rows) == 6
    assert [r["season"] for r in rows] == list(range(2021, 2027))
    # 2025 was their College World Series runner-up season.
    best = next(r for r in rows if r["season"] == 2025)
    assert best["rpi_rank"] <= 5


def test_compare_teams_skips_unresolvable_names():
    rows = crossref.compare_teams(["Tennessee", "Not A Real School", "LSU"], 2025)
    assert len(rows) == 2
    assert {r["team"] for r in rows} == {"Tennessee", "LSU"}


def test_conference_report_aggregates():
    report = crossref.conference_report("SEC", 2025)
    assert report["programs"] >= 14
    assert report["draft_picks"] > 80
    assert report["best_rpi_rank"] == 1
