"""Resolve player-seasons into career entities and assign stable player ids.

    python tools/build_player_registry.py
    python tools/build_player_registry.py --report      # scoring only, no write

The player cache has no cross-season key: a row is a name, a team, and a year.
Anything that needs a career -- counting how many seasons a player has completed,
which is what draft eligibility turns on -- has to reconstruct that identity.

Method
------
A season unit is ``(normalized name, team, year)``, taken across the batting and
pitching caches together, so two-way players resolve once. Units are then merged
by union-find within each name group.

Hard constraints, never violated:

- **C1** Two units in the same year at different teams are different players.
  Mid-season transfers do not happen in NCAA baseball.
- **C2** Two units with known and different birth years are different players.
- **C3** A career may not span more than six years.

Join rules, in priority order, each subject to the constraints:

- **R1** Both units anchor to the same MLBAM id.
- **R2** Same name and equal known birth year -- joins *regardless of team*,
  which is what recovers transfers safely.
- **R3** Same name, same team, and at most two years apart. Two allows one
  redshirt or injury year.
- **R4** Same name, exactly one year apart, one candidate on each side, no birth
  year known for either. **Off by default** (``--permissive``).

Deliberately no fuzzy name matching. Names in this cache do not drift in
spelling, so fuzzy matching here could only manufacture false joins. It belongs
in the MLBAM anchoring step, where two independent sources genuinely disagree.

Strict mode is the default even though the permissive variant scores marginally
better on F1. F1 is the wrong loss here: a false join fabricates a season count
and assigns a wrong birth year to the eligibility engine, producing a
confidently wrong answer. A false split merely truncates a career, which
downstream code can treat as right-censored.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ncaa_bbStats._normalize import normalize_school  # noqa: E402
from ncaa_bbStats._paths import data_path  # noqa: E402

MAX_CAREER_SPAN = 6
MAX_GAP_SAME_TEAM = 2

_SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}


def normalize_name(name: str) -> str:
    """Fold a player name for comparison: lowercase, no punctuation, no suffix."""
    text = normalize_school(name)  # reuses accent folding and punctuation strip
    parts = [p for p in text.split() if p not in _SUFFIXES]
    return " ".join(parts)


class Union:
    """Minimal union-find over hashable keys."""

    def __init__(self):
        self.parent = {}

    def find(self, key):
        self.parent.setdefault(key, key)
        while self.parent[key] != key:
            self.parent[key] = self.parent[self.parent[key]]
            key = self.parent[key]
        return key

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def groups(self):
        out = defaultdict(list)
        for key in self.parent:
            out[self.find(key)].append(key)
        return out


def load_season_units():
    """Every player-season across both caches, as unit records."""
    units = {}
    for stat_type in ("batting", "pitching"):
        path = data_path("player_stats_cache", stat_type, f"{stat_type}.csv")
        if not os.path.isfile(path):
            continue
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row["name"].strip()
                key = (normalize_name(name), row["team"].strip(), int(row["year"]))
                unit = units.setdefault(key, {
                    "name_norm": key[0], "name": name, "team": key[1],
                    "year": key[2], "age": None, "stat_types": set(),
                    "team_name": row.get("team name", ""),
                    "division": int(row.get("division") or 1),
                })
                unit["stat_types"].add(stat_type)
                age = row.get("age")
                if age not in (None, "") and unit["age"] is None:
                    try:
                        unit["age"] = int(float(age))
                    except ValueError:
                        pass
    return units


def load_draft_anchors():
    """Name+school to MLBAM identity, from the public draft records."""
    anchors = []
    directory = data_path("draft_detail")
    if not os.path.isdir(directory):
        return anchors
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(directory, filename), encoding="utf-8") as f:
            for pick in json.load(f):
                if not (pick.get("school_class") or "").startswith(("4YR", "JC")):
                    continue
                anchors.append({
                    "name_norm": normalize_name(pick.get("name") or ""),
                    "mlbam_id": pick.get("mlbam_id"),
                    "birth_date": pick.get("birth_date"),
                    "draft_year": pick.get("year"),
                    "draft_round": pick.get("round"),
                    "draft_pick": pick.get("pick"),
                    "draft_team_id": pick.get("team_id"),
                    "school": pick.get("school"),
                    "school_class": pick.get("school_class"),
                    "height": pick.get("height"),
                    "weight": pick.get("weight"),
                    "position": pick.get("position"),
                    "bats": pick.get("bats"),
                    "throws": pick.get("throws"),
                })
    return anchors


def birth_year(unit):
    """Implied birth year, or None when age is not recorded."""
    return unit["year"] - unit["age"] if unit["age"] is not None else None


def resolve(units, anchor_by_name, permissive=False):
    """Merge season units into career entities. Returns {root: [unit keys]}."""
    union = Union()
    for key in units:
        union.find(key)

    by_name = defaultdict(list)
    for key, unit in units.items():
        by_name[unit["name_norm"]].append(key)

    def compatible(a, b):
        ua, ub = units[a], units[b]
        if ua["year"] == ub["year"] and ua["team"] != ub["team"]:
            return False  # C1
        ba, bb = birth_year(ua), birth_year(ub)
        if ba is not None and bb is not None and ba != bb:
            return False  # C2
        return True

    def try_union(a, b):
        if not compatible(a, b):
            return
        # C3: check the merged span before committing.
        members = union.groups()
        merged = members[union.find(a)] + members[union.find(b)]
        years = [units[k]["year"] for k in merged]
        if max(years) - min(years) > MAX_CAREER_SPAN:
            return
        union.union(a, b)

    for name_norm, keys in by_name.items():
        keys = sorted(keys, key=lambda k: (units[k]["year"], units[k]["team"]))
        anchored = anchor_by_name.get(name_norm)

        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                ua, ub = units[a], units[b]

                # R1: both explained by the same drafted player.
                if anchored and len(anchored) == 1:
                    try_union(a, b)
                    continue
                # R2: same known birth year, regardless of team.
                ba, bb = birth_year(ua), birth_year(ub)
                if ba is not None and ba == bb:
                    try_union(a, b)
                    continue
                # R3: same team, close together.
                if (ua["team"] == ub["team"]
                        and abs(ua["year"] - ub["year"]) <= MAX_GAP_SAME_TEAM):
                    try_union(a, b)
                    continue
                # R4: bare one-year transfer, no age evidence.
                if (permissive and abs(ua["year"] - ub["year"]) == 1
                        and ba is None and bb is None):
                    try_union(a, b)

    return union.groups()


def mint_id(units_for_entity, units):
    """Deterministic seed id from the entity's debut season."""
    debut = min(units_for_entity, key=lambda k: (units[k]["year"], units[k]["team"]))
    unit = units[debut]
    canonical = f"{unit['name_norm']}|{unit['year']}|{unit['team']}"
    digest = hashlib.blake2b(canonical.encode("utf-8"), digest_size=6).hexdigest()
    return f"cbp{digest}"


def build(permissive=False):
    units = load_season_units()
    anchors = load_draft_anchors()

    anchor_by_name = defaultdict(list)
    for anchor in anchors:
        if anchor["name_norm"]:
            anchor_by_name[anchor["name_norm"]].append(anchor)

    groups = resolve(units, anchor_by_name, permissive)

    entities, seasons = [], []
    used_ids = set()
    for root, keys in sorted(groups.items()):
        keys = sorted(keys, key=lambda k: (units[k]["year"], units[k]["team"]))
        members = [units[k] for k in keys]
        years = sorted({m["year"] for m in members})
        teams = sorted({m["team"] for m in members})

        player_id = mint_id(keys, units)
        # Collisions are vanishingly unlikely but must never silently merge two
        # people, so disambiguate rather than trust the hash.
        suffix = 0
        while player_id in used_ids:
            suffix += 1
            player_id = f"{mint_id(keys, units)}-{suffix}"
        used_ids.add(player_id)

        implied = [birth_year(m) for m in members if birth_year(m) is not None]
        anchor = None
        candidates = anchor_by_name.get(members[0]["name_norm"], [])
        # Only accept an anchor whose draft year sits at or just after the
        # player's last college season. The college season ends before the July
        # draft, so a drafted player's final season is the draft year or the one
        # before it.
        for candidate in candidates:
            if candidate["draft_year"] in (max(years), max(years) + 1):
                anchor = candidate
                break

        if anchor and anchor.get("birth_date"):
            birth_est, source = int(anchor["birth_date"][:4]), "mlbam_birth_date"
        elif implied:
            birth_est = int(sorted(implied)[len(implied) // 2])
            source = "median_implied_age"
        else:
            birth_est, source = min(years) - 19, "assumed_freshman"

        stat_types = set()
        for m in members:
            stat_types |= m["stat_types"]
        role = (
            "two_way" if stat_types == {"batting", "pitching"}
            else "pitcher" if stat_types == {"pitching"} else "batter"
        )

        entities.append({
            "player_id": player_id,
            "name": members[-1]["name"],
            "name_norm": members[0]["name_norm"],
            "first_year": min(years),
            "last_year": max(years),
            "n_seasons": len(years),
            "teams": "|".join(teams),
            "primary_role": role,
            "ambiguous": _is_ambiguous(members),
            "birth_year_est": birth_est,
            "birth_year_source": source,
            "birth_date": (anchor or {}).get("birth_date") or "",
            "mlbam_id": (anchor or {}).get("mlbam_id") or "",
            "school_class": (anchor or {}).get("school_class") or "",
            "draft_year": (anchor or {}).get("draft_year") or "",
            "draft_round": (anchor or {}).get("draft_round") or "",
            "draft_pick": (anchor or {}).get("draft_pick") or "",
            "draft_team_id": (anchor or {}).get("draft_team_id") or "",
            "height": (anchor or {}).get("height") or "",
            "weight": (anchor or {}).get("weight") or "",
            "position": (anchor or {}).get("position") or "",
            "bats": (anchor or {}).get("bats") or "",
            "throws": (anchor or {}).get("throws") or "",
            "resolution_method": "strict" if not permissive else "permissive",
        })

        for key in keys:
            unit = units[key]
            seasons.append({
                "player_id": player_id,
                "year": unit["year"],
                "team": unit["team"],
                "division": unit["division"],
                "stat_types": "|".join(sorted(unit["stat_types"])),
                "age": unit["age"] if unit["age"] is not None else "",
            })

    entities.sort(key=lambda e: (e["name_norm"], e["first_year"]))
    seasons.sort(key=lambda s: (s["player_id"], s["year"]))
    return entities, seasons, units, anchor_by_name


def _is_ambiguous(members):
    """True when two units share a name, team and year -- genuine teammates.

    Such an entity must never be joined across years, since there is no evidence
    which of the two same-named players a later season belongs to.
    """
    seen = set()
    for m in members:
        key = (m["team"], m["year"])
        if key in seen:
            return True
        seen.add(key)
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=data_path("player_registry"))
    parser.add_argument("--permissive", action="store_true",
                        help="Enable rule R4. Raises recall, lowers precision.")
    parser.add_argument("--report", action="store_true",
                        help="Report statistics without writing.")
    args = parser.parse_args(argv)

    entities, seasons, units, anchors = build(args.permissive)

    by_seasons = defaultdict(int)
    for entity in entities:
        by_seasons[entity["n_seasons"]] += 1

    print(f"season units:  {len(units)}")
    print(f"entities:      {len(entities)}")
    print(f"  seasons per player: "
          f"{dict(sorted(by_seasons.items()))}")
    print(f"  multi-team careers: "
          f"{sum(1 for e in entities if '|' in e['teams'])}")
    print(f"  two-way:            "
          f"{sum(1 for e in entities if e['primary_role'] == 'two_way')}")
    print(f"  ambiguous:          "
          f"{sum(1 for e in entities if e['ambiguous'])}")
    print(f"  MLBAM anchored:     "
          f"{sum(1 for e in entities if e['mlbam_id'])}")
    sources = defaultdict(int)
    for entity in entities:
        sources[entity["birth_year_source"]] += 1
    print(f"  birth year source:  {dict(sources)}")

    spans = [e["last_year"] - e["first_year"] for e in entities]
    assert max(spans) <= MAX_CAREER_SPAN, "career span constraint violated"

    if args.report:
        print("\n--report: nothing written.")
        return 0

    os.makedirs(args.out, exist_ok=True)
    registry_path = os.path.join(args.out, "player_registry.csv")
    with open(registry_path, "w", newline="\n", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(entities[0].keys()),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(entities)
    print(f"\nwrote {len(entities):6d} -> {os.path.relpath(registry_path)}")

    seasons_path = os.path.join(args.out, "player_seasons.csv")
    with open(seasons_path, "w", newline="\n", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(seasons[0].keys()),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(seasons)
    print(f"wrote {len(seasons):6d} -> {os.path.relpath(seasons_path)}")

    aliases_path = os.path.join(args.out, "player_id_aliases.csv")
    if not os.path.isfile(aliases_path):
        with open(aliases_path, "w", newline="\n", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(["old_id", "new_id", "reason", "release"])
        print(f"created {os.path.relpath(aliases_path)} (empty ledger)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
