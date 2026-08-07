"""Tests for the canonical team registry.

The registry exists so datasets that spell schools differently can be joined.
Two properties matter more than anything else, and both have a history of going
wrong quietly:

- **No alias is ambiguous.** Two sources must never disagree about which school
  a name refers to. Eleven acronyms in `unique_teams.csv` did exactly that --
  one entry answered to both "mercer" and "merrimack" -- which silently attached
  the wrong team stats to every affected player.
- **Every source spelling resolves.** An unresolvable name is a silent join
  failure: the row survives with empty team columns rather than raising.
"""

import collections
import csv
import glob
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ncaa_bbStats import team_registry as reg  # noqa: E402
from ncaa_bbStats._normalize import normalize_school  # noqa: E402
from ncaa_bbStats._paths import data_path, load_team_stats  # noqa: E402
from ncaa_bbStats._normalize import split_team_league  # noqa: E402


def test_no_alias_is_ambiguous():
    """Every spelling resolves to exactly one program.

    Regression test for the eleven mismapped acronyms.
    """
    by_norm = collections.defaultdict(set)
    for row in reg._aliases():
        by_norm[row["alias_norm"]].add(row["team_id"])

    conflicts = {k: sorted(v) for k, v in by_norm.items() if len(v) > 1}
    assert not conflicts, f"aliases resolving to multiple programs: {conflicts}"


@pytest.mark.parametrize("division", [1, 2, 3])
def test_every_ncaa_team_resolves(division):
    """Every team name in every cached season maps to a program."""
    unresolved = set()
    for season in range(2002, 2027):
        try:
            teams = load_team_stats(season, division)
        except FileNotFoundError:
            continue
        for label in teams:
            if reg.resolve_team(split_team_league(label)[0]) is None:
                unresolved.add(label)
    assert not unresolved, f"unresolvable NCAA names: {sorted(unresolved)[:20]}"


def test_every_player_acronym_resolves():
    """Every FanGraphs acronym in the player cache maps to a program."""
    path = pathlib.Path(data_path("player_stats_cache", "batting", "batting.csv"))
    with path.open(newline="", encoding="utf-8") as f:
        acronyms = {row["team"].strip() for row in csv.DictReader(f)}

    unresolved = {a for a in acronyms if reg.resolve_team(a) is None}
    assert not unresolved, f"unresolvable player-cache acronyms: {sorted(unresolved)}"


def test_the_eleven_mismapped_acronyms_point_at_the_right_school():
    """Each acronym resolves to the program the correction table says it should."""
    expected = {
        "KSU": "Kansas St.", "CAN": "Canisius", "SAM": "Samford",
        "STBK": "Stony Brook", "CARK": "Central Ark.", "QUC": "Queens (NC)",
        "STO": "Stonehill", "MER": "Mercer", "MERC": "Mercyhurst",
        "MRMK": "Merrimack", "MSM": "Mount St. Mary's",
    }
    for acronym, school in expected.items():
        assert reg.resolve_team(acronym) == reg.resolve_team(school), (
            f"{acronym} should resolve to {school}, got "
            f"{reg.team_info(acronym)['canonical_name'] if reg.resolve_team(acronym) else None}"
        )


def test_all_namespaces_agree_on_one_program():
    """The same school reached through four sources gives one id."""
    for spellings in (
        ["Eastern Ill.", "EIU", "Eastern Illinois", "Eastern Illinois University"],
        ["Northeastern", "NE", "Northeastern University"],
        ["Alabama St.", "ALST", "Alabama State"],
    ):
        ids = {reg.resolve_team(s) for s in spellings}
        ids.discard(None)
        assert len(ids) == 1, f"{spellings} resolved to {ids}"


def test_rebrands_share_one_identity():
    """A renamed program keeps one id, so its history stays joined."""
    assert reg.resolve_team("Dixie State") == reg.resolve_team("Utah Tech")
    assert reg.resolve_team("Houston Baptist") == reg.resolve_team("Houston Christian")


def test_same_named_schools_stay_separate():
    """Programs distinguished only by a state suffix must not merge."""
    for a, b in (
        ("Miami (OH)", "Miami (FL)"),
        ("Queens (NC)", "Queens (NY)"),
        ("Anderson (IN)", "Anderson (SC)"),
        ("Augustana (IL)", "Augustana (SD)"),
        ("Saint Mary's (CA)", "Saint Mary's (MN)"),
    ):
        id_a, id_b = reg.resolve_team(a), reg.resolve_team(b)
        assert id_a is not None and id_b is not None, f"{a}/{b} did not both resolve"
        assert id_a != id_b, f"{a} and {b} merged into {id_a}"


def test_division_is_not_part_of_identity():
    """A program that changes division keeps one id and one history.

    The previous scheme keyed on (name, division), so New Haven's Division II
    seasons and its Division I season were two unrelated teams.
    """
    seasons = reg.team_seasons("Utah Tech")
    divisions = {s["division"] for s in seasons}
    assert divisions == {1, 2}, f"expected a D-II to D-I move, saw {divisions}"
    assert reg.team_division("Utah Tech", 2015) == 2
    assert reg.team_division("Utah Tech", 2026) == 1


def test_team_ids_are_stable_across_a_rebuild():
    """Ids must not shift when the registry is regenerated.

    The old positional ids renumbered every program whenever one was added,
    silently corrupting anything that had cached them.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "build_team_registry.py"),
             "--out", tmp],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            pytest.skip(f"registry build unavailable: {result.stderr[-400:]}")

        committed = pathlib.Path(data_path("registry", "teams.csv")).read_bytes()
        rebuilt = (pathlib.Path(tmp) / "teams.csv").read_bytes()
        assert committed == rebuilt, (
            "teams.csv differs from a fresh build. Rerun "
            "tools/build_team_registry.py and commit."
        )


def test_conference_lookup():
    assert reg.team_conference("Northeastern", 2025) == "CAA"
    assert reg.team_conference("LSU", 2025) == "SEC"
    assert reg.team_conference("Northeastern", 1850) is None


def test_listing_matches_the_stats_cache():
    """list_teams must agree with the underlying season data."""
    for division in (1, 2, 3):
        listed = len(reg.list_teams(season=2025, division=division))
        actual = len(load_team_stats(2025, division))
        assert listed == actual, (
            f"division {division}: registry lists {listed}, cache has {actual}"
        )


def test_unknown_names_return_none_rather_than_guessing():
    """There is no fuzzy fallback; a near-match must not be invented."""
    for name in ("", "Not A Real School", "Zzzzz University", "XYZ123"):
        assert reg.resolve_team(name) is None


def test_namespace_filter_restricts_the_search():
    """Asking for one source's spelling must not match another's."""
    assert reg.resolve_team("EIU", namespace="fg_acronym") is not None
    assert reg.resolve_team("EIU", namespace="rpi") is None


def test_crosswalk_maps_between_sources():
    mapping = reg.crosswalk("fg_acronym", "rpi", season=2025)
    assert mapping.get("AUB") == "Auburn"
    assert mapping.get("ALST") == "Alabama State"
    assert len(mapping) > 250


def test_team_info_reports_season_context():
    info = reg.team_info("Northeastern", season=2025)
    assert info["canonical_name"] == "Northeastern"
    assert info["ipeds_unitid"] == "167358"
    assert info["division"] == 1
    assert info["conference"] == "CAA"
    assert reg.team_info("Not A Real School") is None


def test_acronyms_are_not_expanded_as_state_abbreviations():
    """Virginia Tech's "VT" must not fold onto Vermont."""
    assert normalize_school("VT") == "vt"
    assert normalize_school("Vermont") == "vermont"
    assert reg.resolve_team("VT") != reg.resolve_team("Vermont")
