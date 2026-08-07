"""Scrape NCAA team stats and write the per-division season cache.

Run as a script; importing this module has no side effects.

    python -m ncaa_bbStats.team_store                    # every season, every division
    python -m ncaa_bbStats.team_store --years 2026
    python -m ncaa_bbStats.team_store --years 2024 2025 2026 --divisions 1
"""

import argparse
import json
import os

from ncaa_bbStats._paths import data_path
from ncaa_bbStats.team_stats import (
    base_on_balls,
    batting_average,
    combine_team_stats,
    double_plays,
    double_plays_per_game,
    doubles,
    doubles_per_game,
    earned_run_average,
    fielding_percentage,
    hit_batters,
    hit_by_pitch,
    hits,
    hits_allowed_per_nine_innings,
    home_runs,
    home_runs_per_game,
    on_base_percentage,
    runs,
    sacrifice_bunts,
    sacrifice_flies,
    scoring,
    shutouts,
    slugging_percentage,
    stolen_bases,
    stolen_bases_per_game,
    strikeout_to_walk_ratio,
    strikeouts_per_nine_innings,
    triple_plays,
    triples,
    triples_per_game,
    walks_allowed_per_nine_innings,
    whip,
    winning_percentage,
)

DEFAULT_YEARS = list(range(2002, 2027))
DEFAULT_DIVISIONS = [1, 2, 3]

# Every stat fetcher that contributes to a cached season. Order is not
# significant; combine_team_stats merges on the (team, league) key.
#
# Previously this was a block of 31 local assignments feeding a hand-written
# list, where `sb` was bound twice -- to sacrifice_bunts and then to
# stolen_bases -- so sacrifice_bunts was silently dropped and stolen_bases was
# merged twice. Naming each fetcher once removes that whole class of mistake.
STAT_FETCHERS = (
    base_on_balls,
    batting_average,
    double_plays,
    double_plays_per_game,
    doubles,
    doubles_per_game,
    earned_run_average,
    fielding_percentage,
    hit_batters,
    hit_by_pitch,
    hits,
    hits_allowed_per_nine_innings,
    home_runs,
    home_runs_per_game,
    on_base_percentage,
    runs,
    sacrifice_bunts,
    sacrifice_flies,
    scoring,
    shutouts,
    slugging_percentage,
    stolen_bases,
    stolen_bases_per_game,
    strikeout_to_walk_ratio,
    strikeouts_per_nine_innings,
    triple_plays,
    triples,
    triples_per_game,
    walks_allowed_per_nine_innings,
    whip,
    winning_percentage,
)


def build_season(year: int, division: int) -> dict:
    """Fetch every stat for one season and merge it into a single mapping.

    Args:
        year (int): The season year (ex. 2026).
        division (int): NCAA division number (1, 2, or 3).

    Returns:
        dict: Mapping of ``"Team (League)"`` to that team's stats, plus a
        ``"division"`` bookkeeping key.
    """
    fetched = [fetcher(year=year, division=division) for fetcher in STAT_FETCHERS]
    # Fetchers return None when the stat did not exist in that season.
    available = [stats for stats in fetched if stats]

    combined = combine_team_stats(*available)
    combined["division"] = int(division)
    return combined


def write_season(year: int, division: int, stats: dict) -> str:
    """Write one season of merged stats to the cache.

    Args:
        year (int): The season year.
        division (int): NCAA division number (1, 2, or 3).
        stats (dict): The merged stat mapping from :func:`build_season`.

    Returns:
        str: The path written.
    """
    output_dir = data_path("team_stats_cache", f"div{division}")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{year}.json")
    with open(output_path, "w") as f:
        json.dump(stats, f)
    return output_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--years", type=int, nargs="+", default=DEFAULT_YEARS,
        help="Seasons to scrape (default: 2002-2026).",
    )
    parser.add_argument(
        "--divisions", type=int, nargs="+", default=DEFAULT_DIVISIONS,
        choices=DEFAULT_DIVISIONS, help="Divisions to scrape (default: 1 2 3).",
    )
    args = parser.parse_args(argv)

    failures = 0
    for year in args.years:
        for division in args.divisions:
            print(f"Scraping data for year: {year}, division: {division}...")
            try:
                stats = build_season(year, division)
            except Exception as e:
                print(f"Skipping year {year}, division {division} due to error: {e}")
                failures += 1
                continue

            # combine_team_stats returns just the sentinel when every fetch
            # failed; writing that would replace a good cache file with an
            # empty one.
            teams = len(stats) - 1
            if teams <= 0:
                print(f"  no teams returned for {year} division {division}, not writing")
                failures += 1
                continue

            path = write_season(year, division, stats)
            print(f"  wrote {teams} teams -> {path}")

    print("Scraping and caching complete!")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
