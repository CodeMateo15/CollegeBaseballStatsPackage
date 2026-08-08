"""Append one season of third-party player exports to ``private/fg/``.

The source site exports a season as four files -- standard and advanced, for
each of the no-minimum and qualified populations -- with title-case headers, a
BOM, and no ``year`` column. The archival files under ``private/fg/`` are one
file per (stat type, qualifier) spanning every season, lowercased, with ``year``
and ``team name`` filled in. This script converts the former into the latter.

    python tools/add_fg_season.py --source-dir "/path/to/2026 data" --year 2026 --check
    python tools/add_fg_season.py --source-dir "/path/to/2026 data" --year 2026

Nothing under ``private/`` is committed or packaged; see tools/README.md. Run
``tools/migrate_fg_to_public.py`` afterwards to regenerate the public caches.

Expected source layout, relative to ``--source-dir``::

    noMin/batting_noMin-standard.csv      noMin/batting_noMin-advanced.csv
    noMin/pitching_noMin-standard.csv     noMin/pitching_noMin-advanced.csv
    qualified/batting_qualified-standard.csv    ... and so on

Standard and advanced are merged on ``playerid``, the vendor's stable key. They
must not be merged on name: the same player is written ``Cam Kozeal`` in one
file and ``Camden Kozeal`` in another, and 16 rows of the 2026 export differ
that way.
"""

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ncaa_bbStats._paths import data_path  # noqa: E402

PRIVATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "private", "fg"
)

STAT_TYPES = ("batting", "pitching")
QUALIFIERS = ("noMin", "qualified")


def read_export(path):
    """Read one vendor CSV. The exports carry a BOM and title-case headers."""
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    if "playerid" not in df.columns:
        raise SystemExit(f"{path}: no playerid column; cannot merge safely.")
    df["playerid"] = df["playerid"].astype(str).str.strip()
    return df


def team_name_map():
    """Acronym -> canonical NCAA team name, from the packaged team registry.

    Deliberately not taken from the vendor's own ``team name`` column: that
    column disagrees with itself across the batting and pitching exports for 13
    acronyms (TAR is both Tarleton State and North Carolina, CAM is both
    Campbell and Cambridge), and the 2026 export omits it entirely. The registry
    is NCAA/IPEDS-sourced and has one name per acronym.
    """
    teams = pd.read_csv(data_path("registry", "teams.csv"))
    aliases = pd.read_csv(data_path("registry", "team_aliases.csv"))
    fg = aliases[aliases["namespace"] == "fg_acronym"].merge(teams, on="team_id")

    conflicts = fg.groupby("alias")["canonical_name"].nunique()
    conflicting = sorted(conflicts[conflicts > 1].index)
    if conflicting:
        raise SystemExit(
            f"registry maps these acronyms to multiple teams: {conflicting}"
        )
    return dict(zip(fg["alias"], fg["canonical_name"]))


def build_season(source_dir, stat_type, qualifier, year, names):
    """Merge the standard and advanced exports for one file into one frame."""
    base = os.path.join(source_dir, qualifier, f"{stat_type}_{qualifier}")
    std_path, adv_path = f"{base}-standard.csv", f"{base}-advanced.csv"
    for path in (std_path, adv_path):
        if not os.path.isfile(path):
            raise SystemExit(f"missing input: {path}")

    std, adv = read_export(std_path), read_export(adv_path)

    # Advanced repeats the identity columns and a few standard stats; keep the
    # standard copy of anything shared so the merge cannot introduce _x/_y pairs.
    overlap = [c for c in adv.columns if c in std.columns and c != "playerid"]
    merged = std.merge(
        adv.drop(columns=overlap), on="playerid", how="left",
        validate="1:1", indicator=True,
    )

    unmatched = int((merged["_merge"] != "both").sum())
    if unmatched:
        raise SystemExit(
            f"{stat_type}/{qualifier}: {unmatched} standard rows have no "
            "advanced counterpart"
        )
    merged = merged.drop(columns="_merge")

    # Some exports carry a redundant "season" column. Use it to confirm --year
    # names the season the files actually hold, then drop it.
    if "season" in merged.columns:
        seasons = set(merged["season"].dropna().astype(int))
        if seasons != {int(year)}:
            raise SystemExit(
                f"{stat_type}/{qualifier}: --year {year} but the export holds "
                f"season(s) {sorted(seasons)}"
            )
        merged = merged.drop(columns="season")

    merged["year"] = int(year)
    unknown = sorted(set(merged["team"].astype(str)) - set(names))
    if unknown:
        raise SystemExit(
            f"{stat_type}/{qualifier}: acronyms absent from the team registry: "
            f"{unknown}. Add them to src/data/registry/team_aliases.csv first."
        )
    merged["team name"] = merged["team"].astype(str).map(names)
    return merged


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-dir", required=True,
                        help="Directory holding noMin/ and qualified/ exports.")
    parser.add_argument("--year", type=int, required=True, help="Season year.")
    parser.add_argument("--check", action="store_true",
                        help="Report what would change without writing.")
    args = parser.parse_args(argv)

    names = team_name_map()
    print(f"team registry: {len(names)} acronyms")

    pending = []
    for stat_type in STAT_TYPES:
        for qualifier in QUALIFIERS:
            season = build_season(args.source_dir, stat_type, qualifier, args.year, names)
            target = os.path.join(PRIVATE_DIR, f"{stat_type}_{qualifier}.csv")
            existing = pd.read_csv(target, encoding="utf-8-sig", low_memory=False)
            existing.columns = [c.strip().lower() for c in existing.columns]

            if args.year in set(existing["year"]):
                raise SystemExit(
                    f"{target} already contains {args.year}. Remove those rows "
                    "first if you mean to replace the season."
                )

            missing = sorted(set(existing.columns) - set(season.columns))
            extra = sorted(set(season.columns) - set(existing.columns))
            if missing or extra:
                raise SystemExit(
                    f"{stat_type}/{qualifier}: column mismatch against {target}\n"
                    f"  missing from the new season: {missing}\n"
                    f"  present only in the new season: {extra}"
                )

            combined = pd.concat([existing, season[existing.columns]], ignore_index=True)
            pending.append((target, combined, len(existing), len(season)))
            print(f"  {stat_type:9s} {qualifier:10s} "
                  f"{len(existing):6,d} + {len(season):5,d} -> {len(combined):6,d} rows")

    if args.check:
        print("\n--check: nothing written.")
        return 0

    for target, combined, _, _ in pending:
        combined.to_csv(target, index=False, lineterminator="\n")
        print(f"wrote {os.path.relpath(target)}")
    print("\nNow run: python tools/migrate_fg_to_public.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
