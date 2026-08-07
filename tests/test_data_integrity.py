"""Invariants on the shipped data caches.

These encode defects that reached a release, so a regression fails loudly:

- Every team-stats JSON carries a `"division": N` bookkeeping key alongside the
  team entries. Iterating `stats.keys()` without filtering it produced a team
  named "division", which is how rows like `1056,division,1` got written into
  data/team_names_stats/all_div_teams.csv.
- `pitching_qualified.csv` was overwritten with the no-minimum data in commit
  a4320ec, so `top_players("pitching", ...)` silently returned unqualified
  results.
- Stripping every parenthesised group from an NCAA label merged genuinely
  distinct schools: Anderson (IN)/(SC), Augustana (IL)/(SD), Miami (OH)/(FL).
"""

import csv
import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ncaa_bbStats import list_all_teams  # noqa: E402
from ncaa_bbStats._normalize import split_team_league  # noqa: E402
from ncaa_bbStats._paths import data_path  # noqa: E402

DIVISIONS = (1, 2, 3)
SEASONS = range(2002, 2027)


@pytest.mark.parametrize("division", DIVISIONS)
@pytest.mark.parametrize("year", SEASONS)
def test_team_stats_cache_parses(year, division):
    path = pathlib.Path(data_path("team_stats_cache", f"div{division}", f"{year}.json"))
    assert path.is_file(), f"missing cache file {path}"
    with path.open() as f:
        stats = json.load(f)
    assert isinstance(stats, dict) and stats


@pytest.mark.parametrize("division", DIVISIONS)
@pytest.mark.parametrize("year", SEASONS)
def test_division_sentinel_never_surfaces_as_a_team(year, division):
    teams = list_all_teams(year, division)
    assert "division" not in teams
    assert all(isinstance(t, str) and t for t in teams)


@pytest.mark.parametrize("division", DIVISIONS)
def test_team_counts_are_plausible(division):
    """Catches a scrape that silently returned a near-empty page."""
    # 2002 is a partial season in the source data (~70-82 teams per division).
    for year in range(2003, 2027):
        count = len(list_all_teams(year, division))
        assert 150 < count < 450, f"div{division} {year} has {count} teams"


def test_split_team_league_keeps_state_disambiguators():
    assert split_team_league("Northeastern (CAA)") == ("Northeastern", "CAA")
    assert split_team_league("Miami (OH) (MAC)") == ("Miami (OH)", "MAC")
    assert split_team_league("Augustana (SD) (NSIC)") == ("Augustana (SD)", "NSIC")
    assert split_team_league("NoParens") == ("NoParens", "")


def test_distinct_schools_are_not_merged_in_team_names():
    """Same-named programs in different states must be separate rows."""
    path = pathlib.Path(data_path("team_names_stats", "all_div_teams.csv"))
    with path.open(newline="", encoding="utf-8") as f:
        names = {row["team_name"] for row in csv.DictReader(f)}

    for a, b in [
        ("Anderson (IN)", "Anderson (SC)"),
        ("Augustana (IL)", "Augustana (SD)"),
        ("Centenary (LA)", "Centenary (NJ)"),
        ("Miami (OH)", "Miami (FL)"),
    ]:
        assert a in names and b in names, f"{a} and {b} should both be present"

    # The bookkeeping key must never have been recorded as a school.
    assert "division" not in names


@pytest.mark.parametrize("stat_type", ["batting", "pitching"])
def test_qualified_is_a_strict_subset(stat_type):
    """The qualified population must be smaller than, and inside, the full one.

    Regression test for a4320ec, which overwrote pitching_qualified.csv with the
    no-minimum data and left the two byte-identical. The two files are now one
    file with a `qualified` flag, which is what makes that failure impossible.
    """
    from ncaa_bbStats.player_utils import list_players

    everyone = set(list_players(stat_type, "noMin"))
    qualified = set(list_players(stat_type, "qualified"))
    assert qualified < everyone, "qualified must be a proper subset of noMin"


@pytest.mark.parametrize("stat_type", ["batting", "pitching"])
def test_player_cache_ships_no_proprietary_columns(stat_type):
    """No third-party derived metric or identifier survives in the cache.

    These are replaced by the c-prefixed metrics in advanced_stats, which this
    package derives itself. See DATA_PROVENANCE.md.
    """
    forbidden = {
        "playerid", "mlbamid", "nameascii",
        "woba", "wrc", "wrc+", "wraa", "wsb", "spd", "fip", "e-f", "lob%",
    }
    path = pathlib.Path(data_path("player_stats_cache", stat_type, f"{stat_type}.csv"))
    with path.open(newline="", encoding="utf-8") as f:
        header = {c.strip().lower() for c in next(csv.reader(f))}

    found = header & forbidden
    assert not found, f"{stat_type}.csv still ships proprietary columns: {sorted(found)}"
