"""Rewrite the player caches as public counting-statistic files.

Reads the private third-party exports under ``private/fg/`` and writes the
redistributable player caches under ``src/data/player_stats_cache/``. See
DATA_PROVENANCE.md for what is removed and why.

    python tools/migrate_fg_to_public.py --check     # report, write nothing
    python tools/migrate_fg_to_public.py

Three things change:

1. **Derived metrics are dropped.** Every rate statistic is pure arithmetic on
   the counting stats -- verified byte-exact against the source, maximum
   difference 0.000000 across 26,826 batting rows -- so storing them adds
   nothing but a way for them to drift. ``ncaa_bbStats.advanced_stats``
   recomputes them on read. Vendor-derived metrics that need proprietary league
   constants (wOBA, wRC+, wRAA, wRC, wSB, Spd, FIP, E-F, LOB%) are replaced by
   package-original NCAA-calibrated equivalents in the same module.

2. **Vendor identifiers are dropped.** ``playerid`` is the source's internal key.
   ``mlbamid`` is re-sourced from the public MLB Stats API in a later step and
   is deliberately renamed ``mlbam_id``, so nothing silently reads the new
   public values through code expecting the old ones.

3. **The qualified/noMin split collapses into one file per stat type** with a
   ``qualified`` boolean. Qualification is per team game (0.7 IP/G pitching,
   2 PA/G batting), so no single threshold reproduces it -- the membership is
   carried over from the source. Two parallel files is what allowed commit
   a4320ec to overwrite ``pitching_qualified.csv`` with the no-minimum data and
   leave ``top_players("pitching", ...)`` silently wrong for five months.
"""

import argparse
import hashlib
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ncaa_bbStats._paths import data_path  # noqa: E402

PRIVATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "private", "fg"
)

# Identity columns kept, in output order.
IDENTITY = ["player_id", "name", "team", "team name", "division", "year", "age"]

# Salt for the player id. The id is derived from the vendor's player key so that
# identity is exact rather than inferred from names, but it is salted so the
# published value is not a bare hash of that key and cannot be dictionary-
# attacked back into it. Changing this renumbers every player; don't.
PLAYER_ID_SALT = b"ncaa_bbStats/player_id/v1"

# Counting statistics kept -- records of what happened on the field.
COUNTING = {
    "batting": ["g", "pa", "ab", "h", "2b", "3b", "hr", "r", "rbi", "bb", "so",
                "hbp", "sf", "sh", "gdp", "sb", "cs"],
    "pitching": ["w", "l", "g", "gs", "cg", "sho", "sv", "ip", "tbf", "h", "r",
                 "er", "hr", "bb", "hbp", "wp", "bk", "so"],
}

# Dropped because they are recomputable from the counting stats above.
RECOMPUTABLE = {
    "batting": ["1b", "avg", "obp", "slg", "ops", "iso", "bb%", "k%", "bb/k", "babip"],
    "pitching": ["era", "whip", "k/9", "bb/9", "k/bb", "hr/9", "k%", "bb%",
                 "k-bb%", "avg", "babip"],
}

# Dropped because they depend on the source's own league constants, weights, or
# park factors. Replaced by the c-prefixed metrics in advanced_stats.
PROPRIETARY = {
    "batting": ["spd", "wsb", "wrc", "wraa", "woba", "wrc+"],
    "pitching": ["lob%", "fip", "e-f"],
}

# Dropped identifiers.
VENDOR_IDS = ["playerid", "mlbamid", "nameascii"]

# Every FanGraphs player row is Division I; their college coverage does not
# extend to Division II or III. Matching acronyms against the multi-division
# name table by a normalized key put 24 of them in the wrong division, and
# division selects the league constants -- a wrong value silently corrupts
# every advanced metric for that team.
PLAYER_DIVISION = 1


def player_id(vendor_id):
    """Package-owned career id for one vendor player key.

    Salted so the published value is not a bare hash of the vendor's internal
    key. Deterministic, so regenerating the caches does not renumber anyone.
    """
    digest = hashlib.blake2b(
        str(vendor_id).strip().encode("utf-8"), key=PLAYER_ID_SALT, digest_size=6
    ).hexdigest()
    return f"cbp{digest}"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(stat_type, qualifier):
    path = os.path.join(PRIVATE_DIR, f"{stat_type}_{qualifier}.csv")
    if not os.path.isfile(path):
        raise SystemExit(
            f"missing input: {path}\n"
            "Populate private/fg/ first; see tools/README.md. The recovered\n"
            "pitching_qualified.csv comes from `git show "
            "7afa3b1:src/data/player_stats_cache/pitching/pitching_qualified.csv`."
        )
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def team_names():
    """Acronym -> canonical NCAA team name, from the packaged team registry.

    The vendor's own ``team name`` column is not trustworthy: it disagrees with
    itself across the batting and pitching exports for 13 acronyms, covering
    ~1,000 rows. TAR is Tarleton State in one file and North Carolina in the
    other; CAM is Campbell in one and Cambridge in the other. In all 13 the
    registry agrees with the batting file, so the pitching values are the wrong
    ones. The 2026 export drops the column entirely.

    ``canonical_name`` is the registry's NCAA display label ("Missouri St.",
    "Saint Mary's (CA)") rather than the IPEDS legal name ("Missouri State
    University-Springfield"). It is the form a team picker wants, and it is
    unambiguous: one name per acronym, asserted below.
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


def build(stat_type):
    """Return (public_dataframe, report_dict) for one stat type."""
    no_min = load(stat_type, "noMin")
    qualified = load(stat_type, "qualified")

    # Keyed on the vendor player id, not the name. The same player is written
    # "Cam Kozeal" in one export and "Camden Kozeal" in the other, and 16 rows
    # of the 2026 season differ that way -- by name they look like players who
    # qualified without appearing in the no-minimum population at all.
    key_cols = ["playerid", "year"]
    qualified_keys = set(map(tuple, qualified[key_cols].values))
    no_min_keys = set(map(tuple, no_min[key_cols].values))
    if not qualified_keys <= no_min_keys:
        raise SystemExit(
            f"{stat_type}: qualified is not a subset of noMin "
            f"({len(qualified_keys - no_min_keys)} rows only in qualified). "
            "The inputs are inconsistent; do not migrate."
        )

    out = no_min.copy()
    out["qualified"] = [tuple(k) in qualified_keys for k in out[key_cols].values]
    out["division"] = PLAYER_DIVISION

    names = team_names()
    unknown = sorted(set(out["team"].astype(str)) - set(names))
    if unknown:
        raise SystemExit(
            f"{stat_type}: acronyms absent from the team registry: {unknown}. "
            "Add them to src/data/registry/team_aliases.csv first."
        )
    out["team name"] = out["team"].astype(str).map(names)

    # A stable career identifier, derived from the vendor's player key so that a
    # career is resolved exactly rather than inferred from names. The previous
    # name|team|year key could not tell the two players named Cole Conn at UIC
    # apart, and could not join "Cam Kozeal" to "Camden Kozeal".
    out["player_id"] = [player_id(pid) for pid in out["playerid"].astype(str)]

    keep = [c for c in IDENTITY + COUNTING[stat_type] + ["qualified"] if c in out.columns]
    dropped = sorted(set(out.columns) - set(keep))
    public = out[keep].sort_values(["year", "team", "name"]).reset_index(drop=True)

    collisions = public.groupby(["player_id", "year"]).size()
    if (collisions > 1).any():
        raise SystemExit(
            f"{stat_type}: a player id repeats within a season: "
            f"{collisions[collisions > 1].index.tolist()[:5]}"
        )

    expected_drops = set(
        RECOMPUTABLE[stat_type] + PROPRIETARY[stat_type] + VENDOR_IDS
    )
    unexpected = sorted(set(dropped) - expected_drops)

    report = {
        "stat_type": stat_type,
        "rows": len(public),
        "qualified_rows": int(public["qualified"].sum()),
        "columns_kept": keep,
        "columns_dropped": dropped,
        "unexpected_drops": unexpected,
        "seasons": sorted(public["year"].unique().tolist()),
        "source_sha256": {
            f"{stat_type}_noMin.csv": sha256(
                os.path.join(PRIVATE_DIR, f"{stat_type}_noMin.csv")
            ),
            f"{stat_type}_qualified.csv": sha256(
                os.path.join(PRIVATE_DIR, f"{stat_type}_qualified.csv")
            ),
        },
    }
    return public, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="Report what would change without writing.")
    args = parser.parse_args(argv)

    reports = []
    for stat_type in ("batting", "pitching"):
        public, report = build(stat_type)
        reports.append(report)

        print(f"\n=== {stat_type} ===")
        print(f"  rows           {report['rows']:,} "
              f"({report['qualified_rows']:,} qualified)")
        print(f"  seasons        {report['seasons']}")
        print(f"  kept    ({len(report['columns_kept']):2d})  "
              f"{', '.join(report['columns_kept'])}")
        print(f"  dropped ({len(report['columns_dropped']):2d})  "
              f"{', '.join(report['columns_dropped'])}")
        if report["unexpected_drops"]:
            print(f"  !! UNEXPECTED DROPS: {report['unexpected_drops']}")
            print("     Add them to COUNTING/RECOMPUTABLE/PROPRIETARY before writing.")
            return 1

        if not args.check:
            out_dir = data_path("player_stats_cache", stat_type)
            os.makedirs(out_dir, exist_ok=True)

            out_path = os.path.join(out_dir, f"{stat_type}.csv")
            public.to_csv(out_path, index=False, lineterminator="\n")
            print(f"  -> {os.path.relpath(out_path)}")

            for stale in (f"{stat_type}_noMin.csv", f"{stat_type}_qualified.csv"):
                stale_path = os.path.join(out_dir, stale)
                if os.path.isfile(stale_path):
                    os.remove(stale_path)
                    print(f"  removed {os.path.relpath(stale_path)}")

    if args.check:
        print("\n--check: nothing written.")
        return 0

    manifest_path = data_path("player_stats_cache", "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "generator": "tools/migrate_fg_to_public.py",
            "note": "Counting statistics only. Rate and advanced metrics are "
                    "computed on read by ncaa_bbStats.advanced_stats. See "
                    "DATA_PROVENANCE.md.",
            "datasets": reports,
        }, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"\nwrote {os.path.relpath(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
