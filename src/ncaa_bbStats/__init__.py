"""Retrieval and analysis of NCAA college baseball statistics.

Team stats (Divisions I-III, 2002-2026), player stats (2021-2025), and MLB draft
history (1965-2025). See https://collegebaseballstatspackage.readthedocs.io.

Names are re-exported flat, so ``from ncaa_bbStats import get_team_stat`` works.
Submodules are also importable directly (``ncaa_bbStats.player_utils``) for
callers who prefer a namespace.
"""

import importlib

from ncaa_bbStats.utils import (
    compare_pythagorean_expectation,
    display_specific_team_stat,
    display_team_stats,
    get_drafted_players_all_years_college,
    get_drafted_players_all_years_mlb,
    get_drafted_players_college,
    get_drafted_players_mlb,
    get_pythagorean_expectation,
    get_team_stat,
    list_all_teams,
    plot_team_stat_over_years,
    print_draft_picks_college,
    print_draft_picks_mlb,
)

from ncaa_bbStats.average import (
    average_all_team_stats,
    average_team_stat_float,
    average_team_stat_str,
)

from ncaa_bbStats.player_utils import (
    batting_stat,
    get_player_rows,
    list_available_years,
    list_batters,
    list_pitchers,
    list_players,
    load_player_frame,
    pitching_stat,
    player_seasons,
    top_players,
)

from ncaa_bbStats.team_registry import (
    crosswalk,
    list_conferences,
    list_teams,
    resolve_team,
    resolve_team_verbose,
    team_aliases,
    team_conference,
    team_division,
    team_info,
    team_seasons,
)

from ncaa_bbStats.advanced_stats import (
    cfip,
    clob_pct,
    cspd,
    cwoba,
    cwraa,
    cwrc,
    cwrc_plus,
    cwsb,
    league_constants,
    seasons_with_constants,
)

# Names whose defining module imports an optional dependency at module scope.
# Importing them eagerly makes `import ncaa_bbStats` fail on a clean install
# when that extra is absent -- draft_stats imports requests and bs4, which are
# only pulled in by the [scrape] extra. PEP 562 defers the cost to first use.
_LAZY_ATTRS = {
    "parse_mlb_draft": "ncaa_bbStats.draft_stats",
}

__all__ = [
    # utils -- team stats
    "get_team_stat",
    "display_specific_team_stat",
    "display_team_stats",
    "list_all_teams",
    "plot_team_stat_over_years",
    "get_pythagorean_expectation",
    "compare_pythagorean_expectation",
    # utils -- draft
    "get_drafted_players_mlb",
    "get_drafted_players_all_years_mlb",
    "get_drafted_players_college",
    "get_drafted_players_all_years_college",
    "print_draft_picks_mlb",
    "print_draft_picks_college",
    # average
    "average_all_team_stats",
    "average_team_stat_str",
    "average_team_stat_float",
    # player_utils
    "list_available_years",
    "list_players",
    "player_seasons",
    "get_player_rows",
    "load_player_frame",
    "top_players",
    "batting_stat",
    "pitching_stat",
    "list_batters",
    "list_pitchers",
    # team_registry -- canonical identity across every data source
    "resolve_team",
    "resolve_team_verbose",
    "team_info",
    "team_aliases",
    "team_seasons",
    "team_division",
    "team_conference",
    "list_teams",
    "list_conferences",
    "crosswalk",
    # advanced_stats -- derived by this package, see DATA_PROVENANCE.md
    "cwoba",
    "cwraa",
    "cwrc",
    "cwrc_plus",
    "cwsb",
    "cspd",
    "cfip",
    "clob_pct",
    "league_constants",
    "seasons_with_constants",
    # draft_stats (lazy)
    "parse_mlb_draft",
]


def __getattr__(name):
    """Resolve lazily-loaded public names on first access (PEP 562)."""
    module_name = _LAZY_ATTRS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(module_name), name)
    globals()[name] = value  # cache so __getattr__ runs once per name
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
