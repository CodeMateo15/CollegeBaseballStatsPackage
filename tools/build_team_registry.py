"""Build the canonical team registry.

    python tools/build_team_registry.py
    python tools/build_team_registry.py --report    # show what fails to resolve

Four sources spell schools four different ways, and nothing joins without a
common key:

    NCAA team stats     "Eastern Ill. (MVC)"          short names + league
    FanGraphs players   "EIU"                         acronyms
    Baseball Almanac    "Eastern Illinois University"  legal names
    Warren Nolan RPI    "Eastern Illinois"             spelled-out names
    EADA / IPEDS        "Eastern Illinois University"  charter names

This assigns every program one `team_id` and records each source's spelling as
an alias, so a lookup in any namespace lands on the same program.

Identity notes
--------------
The canonical key is the federal IPEDS unitid where one is known, because it
survives rebrands -- Houston Baptist and Houston Christian share a unitid.
Programs with no unitid get a minted `NCAA:<slug>` id, frozen on first
assignment.

Division is deliberately *not* part of identity. It is recorded per season in
team_seasons.csv, so a program that moves up (New Haven, Division II through
2025 and Division I in 2026) keeps one id and one history. The previous scheme
enumerated `sorted(set((name, division)))` and used the row number as the id,
which both split such programs in two and renumbered everything whenever a team
was added.
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ncaa_bbStats._normalize import normalize_school, split_team_league  # noqa: E402
from ncaa_bbStats._paths import data_path, load_team_stats  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PRIVATE_REFERENCE = os.path.join(HERE, "..", "private", "reference")

SEASONS = range(2002, 2027)
DIVISIONS = (1, 2, 3)

# One namespace per source. Keeping them separate means a bad alias in one
# source cannot poison lookups in another.
NAMESPACES = (
    "ncaa_short",        # NCAA team stats, e.g. "Eastern Ill."
    "ncaa_label",        # NCAA team stats with league, e.g. "Eastern Ill. (MVC)"
    "fg_acronym",        # player leaderboards, e.g. "EIU"
    "fg_full",           # player leaderboards, full name
    "rpi",               # Warren Nolan
    "eada_institution",  # IPEDS charter name
    "almanac_school",    # Baseball Almanac draft records
)

OPEN_ENDED = 9999


def slugify(name: str) -> str:
    """Stable, readable id fragment for a program with no IPEDS unitid."""
    return re.sub(r"[^a-z0-9]+", "-", normalize_school(name)).strip("-")


def read_csv(path, required=True):
    if not os.path.isfile(path):
        if required:
            raise SystemExit(
                f"missing reference file: {path}\nSee tools/README.md."
            )
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def collect_ncaa_seasons():
    """Every (program, season, division, league) the team caches record."""
    rows = []
    for division in DIVISIONS:
        for season in SEASONS:
            try:
                teams = load_team_stats(season, division)
            except FileNotFoundError:
                continue
            for label in teams:
                name, league = split_team_league(label)
                rows.append({
                    "ncaa_short": name,
                    "ncaa_label": label,
                    "season": season,
                    "division": division,
                    "league": league,
                })
    return rows


def build_programs(ncaa_rows, crosswalk, manual_rows=()):
    """Group NCAA names into programs and assign canonical ids.

    Args:
        ncaa_rows (list[dict]): Output of :func:`collect_ncaa_seasons`.
        crosswalk (list[dict]): eada_crosswalk rows carrying unitids.
        manual_rows (list[dict]): Hand-written alias rows. Consulted here so a
            program whose unitid is only reachable through an alias still gets
            an IPEDS id rather than a minted one -- Miami (FL) appears in the
            crosswalk only as "University of Miami".

    Returns:
        tuple: ``(programs, key_to_id)`` where programs maps team_id to a record.
    """
    # NCAA short name -> IPEDS unitid, via the crosswalk's own NCAA spelling.
    unitid_by_key = {}
    institution_by_key = {}
    state_by_key = {}
    for row in crosswalk:
        unitid = (row.get("unitid") or "").strip()
        if not unitid:
            continue
        for field in ("team_old", "full_name", "institution_name"):
            value = (row.get(field) or "").strip()
            if value:
                unitid_by_key.setdefault(normalize_school(value), unitid)
        institution_by_key[unitid] = (row.get("institution_name") or "").strip()
        state_by_key[unitid] = (row.get("state_cd") or "").strip()

    # Route each manual alias's unitid to the NCAA spelling it belongs to.
    for row in manual_rows:
        alias_key = normalize_school(row.get("alias", ""))
        target_key = normalize_school(row.get("resolve_via", ""))
        if alias_key in unitid_by_key and target_key:
            unitid_by_key.setdefault(target_key, unitid_by_key[alias_key])

    # Group by folded name, so a program is one entity across divisions.
    by_key = defaultdict(list)
    for row in ncaa_rows:
        by_key[normalize_school(row["ncaa_short"])].append(row)

    programs = {}
    key_to_id = {}
    for key, rows in sorted(by_key.items()):
        unitid = unitid_by_key.get(key)
        if unitid:
            team_id = f"IPEDS:{unitid}"
            id_source = "ipeds"
        else:
            team_id = f"NCAA:{slugify(rows[0]['ncaa_short'])}"
            id_source = "minted"

        # Prefer the spelling used most recently as the display name.
        canonical = max(rows, key=lambda r: r["season"])["ncaa_short"]
        seasons = sorted({r["season"] for r in rows})
        divisions = sorted({r["division"] for r in rows})

        if team_id in programs:
            # Two NCAA spellings resolving to one unitid: merge.
            existing = programs[team_id]
            existing["seasons"] = sorted(set(existing["seasons"]) | set(seasons))
            existing["divisions"] = sorted(set(existing["divisions"]) | set(divisions))
            existing["ncaa_rows"].extend(rows)
        else:
            programs[team_id] = {
                "team_id": team_id,
                "canonical_name": canonical,
                "ipeds_unitid": unitid or "",
                "institution_name": institution_by_key.get(unitid, ""),
                "state": state_by_key.get(unitid, ""),
                "id_source": id_source,
                "seasons": seasons,
                "divisions": divisions,
                "ncaa_rows": rows,
            }
        key_to_id[key] = team_id

    return programs, key_to_id


def add_alias(aliases, team_id, alias, namespace, source,
              valid_from=0, valid_to=OPEN_ENDED):
    """Record one source spelling, skipping exact duplicates."""
    alias = (alias or "").strip()
    if not alias:
        return
    normalized = normalize_school(alias)
    if not normalized:
        return
    entry = (team_id, alias, normalized, namespace, valid_from, valid_to, source)
    aliases.add(entry)


def resolve(key_to_id, name):
    """Look up a folded name, returning the team_id or None."""
    return key_to_id.get(normalize_school(name))


def build(report_only=False):
    ncaa_rows = collect_ncaa_seasons()
    crosswalk = read_csv(os.path.join(PRIVATE_REFERENCE, "eada_crosswalk.csv"),
                         required=False)
    manual_rows = read_csv(os.path.join(HERE, "team_aliases_manual.csv"),
                           required=False)
    programs, key_to_id = build_programs(ncaa_rows, crosswalk, manual_rows)

    aliases = set()
    unresolved = defaultdict(set)

    # Hand-written aliases load first, so the source passes below can resolve
    # through them. Each names the NCAA spelling it belongs to rather than a raw
    # team_id, which keeps the file readable and stable if an id ever changes.
    manual_validity = {}
    for row in manual_rows:
        team_id = resolve(key_to_id, row["resolve_via"])
        if not team_id:
            unresolved["manual"].add(f"{row['alias']} -> {row['resolve_via']}")
            continue
        valid_from = int(row["valid_from"]) if row.get("valid_from") else 0
        valid_to = int(row["valid_to"]) if row.get("valid_to") else OPEN_ENDED
        add_alias(aliases, team_id, row["alias"], row["namespace"],
                  "team_aliases_manual.csv", valid_from, valid_to)
        # Make it resolvable for the passes that follow.
        key_to_id.setdefault(normalize_school(row["alias"]), team_id)
        manual_validity[normalize_school(row["alias"])] = (valid_from, valid_to)

    # NCAA -- always resolves, it is what defined the programs.
    for row in ncaa_rows:
        team_id = key_to_id[normalize_school(row["ncaa_short"])]
        add_alias(aliases, team_id, row["ncaa_short"], "ncaa_short",
                  "team_stats_cache")
        add_alias(aliases, team_id, row["ncaa_label"], "ncaa_label",
                  "team_stats_cache")

    # IPEDS / EADA institution names.
    for row in crosswalk:
        team_id = resolve(key_to_id, row.get("team_old", ""))
        if not team_id:
            unresolved["eada_institution"].add(row.get("team_old", ""))
            continue
        add_alias(aliases, team_id, row.get("institution_name", ""),
                  "eada_institution", "eada_crosswalk.csv")
        add_alias(aliases, team_id, row.get("full_name", ""), "fg_full",
                  "eada_crosswalk.csv")
        add_alias(aliases, team_id, row.get("team", ""), "fg_acronym",
                  "eada_crosswalk.csv")

    # FanGraphs acronym table shipped with the player cache. Resolve by acronym
    # first: the crosswalk pass above already tied acronyms to programs via the
    # NCAA spelling, and the full names here are legal names ("Alcorn State
    # University") that do not fold onto NCAA short names ("Alcorn").
    id_by_acronym = {
        entry[2]: entry[0] for entry in aliases if entry[3] == "fg_acronym"
    }
    acronyms = read_csv(data_path("player_stats_cache", "batting",
                                  "unique_teams.csv"), required=False)
    for row in acronyms:
        full = row.get("Full Name") or row.get("full name") or ""
        acronym = row.get("Acronym") or row.get("acronym") or ""
        team_id = (
            id_by_acronym.get(normalize_school(acronym))
            or resolve(key_to_id, full)
        )
        if not team_id:
            unresolved["fg_acronym"].add(f"{acronym} ({full})")
            continue
        add_alias(aliases, team_id, full, "fg_full", "unique_teams.csv")
        add_alias(aliases, team_id, acronym, "fg_acronym", "unique_teams.csv")

    # Warren Nolan RPI spellings, if the RPI data has been staged.
    rpi_dir = os.path.join(PRIVATE_REFERENCE, "rpi")
    if os.path.isdir(rpi_dir):
        for filename in sorted(os.listdir(rpi_dir)):
            if not filename.endswith(".csv"):
                continue
            season = int(re.search(r"(\d{4})", filename).group(1))
            for row in read_csv(os.path.join(rpi_dir, filename)):
                name = row.get("Team", "")
                team_id = resolve(key_to_id, name)
                if not team_id:
                    unresolved["rpi"].add(name)
                    continue
                validity = manual_validity.get(normalize_school(name))
                if validity and not (validity[0] <= season <= validity[1]):
                    # A retired spelling appearing outside its stated window is
                    # a data problem, not something to silently widen.
                    unresolved["rpi_out_of_window"].add(f"{name} in {season}")
                    continue
                add_alias(aliases, team_id, name, "rpi", filename,
                          season, season)

    return programs, aliases, ncaa_rows, key_to_id, unresolved


def audit_ambiguity(aliases):
    """Return normalized aliases that resolve to more than one program.

    Any hit here is a data error, not genuine ambiguity: it means two sources
    disagree about which school a name refers to. This is how the eleven
    mismapped acronyms in unique_teams.csv were caught -- one entry had a single
    program answering to both "mercer" and "merrimack".

    Args:
        aliases (set): Alias tuples as built by :func:`add_alias`.

    Returns:
        dict: ``{alias_norm: sorted list of team_ids}`` for each conflict.
    """
    by_norm = defaultdict(set)
    for team_id, _alias, alias_norm, _namespace, _from, _to, _source in aliases:
        by_norm[alias_norm].add(team_id)
    return {k: sorted(v) for k, v in by_norm.items() if len(v) > 1}


def write_registry(programs, aliases, ncaa_rows, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    teams_path = os.path.join(out_dir, "teams.csv")
    with open(teams_path, "w", newline="\n", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["team_id", "canonical_name", "ipeds_unitid",
                         "institution_name", "state", "id_source",
                         "first_season", "last_season", "divisions"])
        for program in sorted(programs.values(), key=lambda p: p["team_id"]):
            writer.writerow([
                program["team_id"], program["canonical_name"],
                program["ipeds_unitid"], program["institution_name"],
                program["state"], program["id_source"],
                min(program["seasons"]), max(program["seasons"]),
                "|".join(str(d) for d in program["divisions"]),
            ])

    aliases_path = os.path.join(out_dir, "team_aliases.csv")
    with open(aliases_path, "w", newline="\n", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["team_id", "alias", "alias_norm", "namespace",
                         "valid_from", "valid_to", "source"])
        writer.writerows(sorted(aliases))

    seasons_path = os.path.join(out_dir, "team_seasons.csv")
    seen = set()
    with open(seasons_path, "w", newline="\n", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["team_id", "season", "division", "league",
                         "ncaa_short", "ncaa_label"])
        for program in sorted(programs.values(), key=lambda p: p["team_id"]):
            for row in sorted(program["ncaa_rows"],
                              key=lambda r: (r["season"], r["division"])):
                key = (program["team_id"], row["season"], row["division"])
                if key in seen:
                    continue
                seen.add(key)
                writer.writerow([
                    program["team_id"], row["season"], row["division"],
                    row["league"], row["ncaa_short"], row["ncaa_label"],
                ])

    return {
        "teams.csv": len(programs),
        "team_aliases.csv": len(aliases),
        "team_seasons.csv": len(seen),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=data_path("registry"))
    parser.add_argument("--report", action="store_true",
                        help="Report unresolved names and write nothing.")
    args = parser.parse_args(argv)

    programs, aliases, ncaa_rows, key_to_id, unresolved = build(args.report)

    print(f"programs:      {len(programs)}")
    print(f"  with IPEDS unitid: "
          f"{sum(1 for p in programs.values() if p['ipeds_unitid'])}")
    print(f"  minted NCAA ids:   "
          f"{sum(1 for p in programs.values() if not p['ipeds_unitid'])}")
    print(f"aliases:       {len(aliases)}")
    by_namespace = defaultdict(int)
    for entry in aliases:
        by_namespace[entry[3]] += 1
    for namespace, count in sorted(by_namespace.items()):
        print(f"  {namespace:20s} {count}")

    if unresolved:
        print("\nunresolved source spellings:")
        for namespace, names in sorted(unresolved.items()):
            print(f"  {namespace} ({len(names)}): {sorted(names)[:12]}")

    conflicts = audit_ambiguity(aliases)
    if conflicts:
        print(f"\nAMBIGUOUS ALIASES ({len(conflicts)}) -- two sources disagree "
              "about which school a name refers to:")
        for alias_norm, team_ids in sorted(conflicts.items()):
            names = [programs[t]["canonical_name"] for t in team_ids if t in programs]
            print(f"  {alias_norm!r} -> {list(zip(team_ids, names))}")
        print("\nRefusing to write. Fix the source table or add a manual alias.")
        return 1

    if args.report:
        print("\n--report: nothing written.")
        return 0

    counts = write_registry(programs, aliases, ncaa_rows, args.out)
    for name, count in counts.items():
        print(f"\nwrote {count:5d} rows -> "
              f"{os.path.relpath(os.path.join(args.out, name))}")

    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({
            "generator": "tools/build_team_registry.py",
            "namespaces": list(NAMESPACES),
            "programs": len(programs),
            "with_ipeds_unitid": sum(
                1 for p in programs.values() if p["ipeds_unitid"]
            ),
            "note": "Division is a season attribute, not part of identity. "
                    "See team_seasons.csv.",
        }, f, indent=2, sort_keys=True)
        f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
