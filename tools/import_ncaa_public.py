"""Import the NCAA-sourced player caches, replacing the third-party dependency.

Reads the public player-season files produced by
``ncaaBaseballDraft-Predictor/CSV+Code Files/ncaa_scraper`` and writes a second
player cache under ``src/data/player_stats_cache_ncaa/``. See DATA_PROVENANCE.md.

    python tools/import_ncaa_public.py --check                 # report only
    python tools/import_ncaa_public.py --source-dir <path>

**This is the "Planned" item in README.md finally landing.** DATA_PROVENANCE.md has
carried this caveat since 1.2.0:

    "But their *provenance in this package* is still a FanGraphs export, even
    though the underlying facts are not FanGraphs'. Re-deriving them directly from
    stats.ncaa.org individual-player pages is planned, and would remove the
    dependency entirely."

That is what these files are. The counting statistics here were never touched by a
FanGraphs export: they come from NCAA's own published season statistics, and the
rate and run-value columns were re-derived from them.

**Why this writes a SECOND cache rather than overwriting the first.** Two columns
the existing cache carries cannot be sourced publicly at all:

* ``age`` -- NCAA publishes class year, never a date of birth. There is no public
  DOB for college players anywhere, so this column is empty here. It is a model
  feature (``features.BIO_FEATURES``), so swapping the default source without
  retraining would quietly feed the model an all-null feature.
* **2026** -- the upstream NCAA mirrors stopped updating on 2026-04-12, mid-season,
  so their 2026 holds roughly 60% of a season. Coverage here is 2021-2025, while
  the existing cache runs 2021-2026 and the draft app defaults to 2026.

So the old cache stays exactly where it is and stays the default. This one is
opt-in via ``load_player_frame(..., source="ncaa")`` until the models are retrained
and the app's season list is reconciled. Nothing is deleted.

What this cache does carry that the old one does not: a ``class`` column (the
public substitute for ``age``, and the criterion draft eligibility actually turns
on), and ``person_id``, a cross-season player key. That second one matters -- NCAA
mints a *new* player id every season, so its own id cannot group a player across
years.
"""

import argparse
import hashlib
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from ncaa_bbStats._paths import data_path  # noqa: E402

# Default location of the sibling research repository that produces the files.
DEFAULT_SOURCE = os.path.join(
    os.path.expanduser("~"), "ncaaBaseballDraft-Predictor",
    "CSV+Code Files", "ncaa_public")

CACHE_DIR = "player_stats_cache_ncaa"

# The existing cache's column contract, which this output matches so that
# player_utils and advanced_stats need no special case. `age` is present but empty;
# `class` and `person_id` are additions.
IDENTITY = ["player_id", "person_id", "name", "team", "team name", "division",
            "year", "age", "class"]

COUNTING = {
    "batting": ["g", "pa", "ab", "h", "2b", "3b", "hr", "r", "rbi", "bb", "so",
                "hbp", "sf", "sh", "gdp", "sb", "cs"],
    "pitching": ["w", "l", "g", "gs", "cg", "sho", "sv", "ip", "tbf", "h", "r",
                 "er", "hr", "bb", "hbp", "wp", "bk", "so"],
}

# Recomputed on read by ncaa_bbStats.advanced_stats, so storing them here would
# only give them a way to drift. Identical reasoning to migrate_fg_to_public.py.
RECOMPUTABLE = {
    "batting": ["1b", "avg", "obp", "slg", "ops", "iso", "bb%", "k%", "bb/k",
                "babip", "spd", "wsb", "wrc", "wraa", "woba", "wrc+"],
    "pitching": ["era", "whip", "k/9", "bb/9", "k/bb", "hr/9", "k%", "bb%",
                 "k-bb%", "avg", "babip", "lob%", "fip", "e-f"],
}

# Source-side identity columns not carried through. `playerid` is NCAA's
# per-season key, superseded here by `person_id`; `nameascii` is a fold of `name`.
SOURCE_IDS = ["playerid", "nameascii"]

# Qualification is a rate per team game, fitted against the vendor's own qualified
# leaderboards and frozen. Same constants the research repository uses.
QUALIFICATION_RATES = {"batting": 2.70, "pitching": 0.80}

PLAYER_DIVISION = 1


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def team_names():
    """Acronym -> registry canonical name.

    Lifted from migrate_fg_to_public.team_names() so both caches label teams
    identically. The source files carry no team-name column at all, which removes
    the disagreement that function had to work around.
    """
    teams = pd.read_csv(data_path("registry", "teams.csv"))
    aliases = pd.read_csv(data_path("registry", "team_aliases.csv"))
    fg = aliases[aliases["namespace"] == "fg_acronym"].merge(teams, on="team_id")
    conflicts = fg.groupby("alias")["canonical_name"].nunique()
    conflicting = sorted(conflicts[conflicts > 1].index)
    if conflicting:
        raise SystemExit(
            f"registry maps these acronyms to multiple teams: {conflicting}")
    return dict(zip(fg["alias"], fg["canonical_name"]))


def ip_to_true(value):
    """NCAA thirds notation (97.2 = 97 2/3) to true innings, for qualification."""
    if pd.isna(value):
        return float("nan")
    whole = int(float(value))
    tenths = round(float(value) - whole, 1)
    if tenths == 0.1:
        return whole + 1.0 / 3.0
    if tenths == 0.2:
        return whole + 2.0 / 3.0
    return float(whole)


def load_team_games(source_dir):
    """Games played per (team, year), from the batting file's per-team maximum."""
    path = os.path.join(source_dir, "batting_combined_all.csv")
    frame = pd.read_csv(path, usecols=["team", "year", "g"], low_memory=False)
    return (frame.dropna(subset=["g"]).groupby(["team", "year"])["g"]
            .max().rename("team_g"))


def build(stat_type, source_dir, names, team_games):
    """Return (dataframe, report) for one stat type."""
    path = os.path.join(source_dir, f"{stat_type}_combined_all.csv")
    if not os.path.isfile(path):
        raise SystemExit(
            f"missing {path}\nBuild it first:\n"
            f"  cd <research repo>/CSV+Code Files/ncaa_scraper\n"
            f"  python run.py --years 2021-2025")
    frame = pd.read_csv(path, low_memory=False)
    frame.columns = [c.strip() for c in frame.columns]

    missing = [c for c in COUNTING[stat_type] if c not in frame.columns]
    if missing:
        raise SystemExit(f"{stat_type}: source is missing {missing}")

    out = pd.DataFrame(index=frame.index)
    # `person_id` is the cross-season key and becomes this cache's `player_id`,
    # prefixed so it can never be confused with the other cache's ids -- those are
    # a hash of a FanGraphs key and refer to a different id space entirely.
    out["player_id"] = frame["person_id"].map(
        lambda v: f"n_{v}" if pd.notna(v) else pd.NA)
    out["person_id"] = frame["person_id"]
    out["name"] = frame["name"]
    out["team"] = frame["team"]
    out["team name"] = frame["team"].map(names)
    out["division"] = PLAYER_DIVISION
    out["year"] = frame["year"]
    # Empty by necessity, not oversight. See the module docstring.
    out["age"] = pd.NA
    out["class"] = frame["class"]
    for column in COUNTING[stat_type]:
        out[column] = frame[column]

    unknown = sorted(set(frame["team"]) - set(names))
    if unknown:
        raise SystemExit(
            f"{stat_type}: these team acronyms are not in the registry: "
            f"{unknown}\nAdd them to src/data/registry/team_aliases.csv first.")

    # Qualification: a rate per team game. `team_games` is derived ONCE from the
    # batting file, because there a player's `g` is games appeared in and its
    # per-team maximum is the team's schedule length. Deriving it from the pitching
    # file instead uses pitcher *appearances* -- a maximum near 30 rather than 56 --
    # which made the threshold roughly half what it should be and flagged 14,171
    # pitchers as qualified against the correct 5,651.
    merged = out.merge(team_games, left_on=["team", "year"], right_index=True,
                       how="left")
    if stat_type == "batting":
        stat = pd.to_numeric(merged["pa"], errors="coerce")
    else:
        stat = merged["ip"].map(ip_to_true)
    out["qualified"] = (stat >= merged["team_g"]
                        * QUALIFICATION_RATES[stat_type]).fillna(False).values

    unrostered = int(out["player_id"].isna().sum())
    out = out.sort_values(["year", "team", "name"]).reset_index(drop=True)

    dropped = sorted(set(frame.columns) - set(out.columns))
    expected = set(RECOMPUTABLE[stat_type] + SOURCE_IDS)
    unexpected = sorted(set(dropped) - expected)

    report = {
        "stat_type": stat_type,
        "rows": int(len(out)),
        "qualified_rows": int(out["qualified"].sum()),
        "seasons": sorted(int(y) for y in out["year"].unique()),
        "teams": int(out["team"].nunique()),
        "columns_kept": list(out.columns),
        "unexpected_drops": unexpected,
        "rows_without_person_id": unrostered,
        "source_file": os.path.basename(path),
        "source_sha256": sha256(path),
        "qualification_rate_per_team_game": QUALIFICATION_RATES[stat_type],
    }
    return out, report


def upstream_provenance(source_dir):
    """Pull the pinned upstream commits from the research repo's bulk manifest.

    This is the citation that matters: the mirrors are mutable GitHub repositories,
    so naming them is not enough -- the commit and the file hash are what make the
    numbers reproducible.
    """
    path = os.path.join(source_dir, "BULK_MANIFEST.json")
    if not os.path.isfile(path):
        return {"note": f"{os.path.basename(path)} not found beside the source files"}
    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    resolved = manifest.get("resolved", {})
    return {
        "repositories": {
            alias: {
                "url": f"https://github.com/{entry['owner']}/{entry['repo']}",
                "commit": entry["sha"],
                "resolved_at": entry.get("resolved_at"),
            }
            for alias, entry in sorted(resolved.items())
        },
        "files": len(manifest.get("files", {})),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE,
                        help=f"directory holding the public player CSVs "
                             f"(default: {DEFAULT_SOURCE})")
    parser.add_argument("--check", action="store_true",
                        help="report only; write nothing")
    args = parser.parse_args(argv)

    names = team_names()
    team_games = load_team_games(args.source_dir)
    reports = []
    for stat_type in ("batting", "pitching"):
        frame, report = build(stat_type, args.source_dir, names, team_games)
        reports.append(report)
        print(f"{stat_type}: {report['rows']:,} rows, "
              f"{report['qualified_rows']:,} qualified, "
              f"{report['teams']} teams, seasons {report['seasons']}")
        if report["unexpected_drops"]:
            print(f"  ! unexpected drops: {report['unexpected_drops']}")
        if report["rows_without_person_id"]:
            print(f"  {report['rows_without_person_id']} row(s) have no "
                  f"cross-season key (no roster entry upstream)")

        if not args.check:
            out_dir = data_path(CACHE_DIR, stat_type)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{stat_type}.csv")
            frame.to_csv(out_path, index=False, lineterminator="\n")
            print(f"  -> {os.path.relpath(out_path)}")

    if args.check:
        print("\n--check: nothing written.")
        return 0

    manifest_path = data_path(CACHE_DIR, "manifest.json")
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump({
            "generator": "tools/import_ncaa_public.py",
            "note": "Counting statistics only, sourced from NCAA's own published "
                    "season statistics with no third-party export in the chain. "
                    "Rate and advanced metrics are computed on read by "
                    "ncaa_bbStats.advanced_stats. `age` is empty because NCAA "
                    "publishes class year, not date of birth. See "
                    "DATA_PROVENANCE.md.",
            "source": "ncaaBaseballDraft-Predictor/CSV+Code Files/ncaa_scraper",
            "upstream": upstream_provenance(args.source_dir),
            "datasets": reports,
        }, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"\nwrote {os.path.relpath(manifest_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
