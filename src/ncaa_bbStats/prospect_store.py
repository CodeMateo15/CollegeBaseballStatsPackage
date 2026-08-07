"""Cache MLB Pipeline top-250 draft prospect rankings.

Run as a script; importing this module has no side effects.

    python -m ncaa_bbStats.prospect_store --from-dir path/to/mlb_draft_prospects

These are pre-draft rankings published by MLB Pipeline. They are useful mainly
as a benchmark: comparing a model's ordering against a scouting consensus, and
comparing both against where players actually went.

Schools are resolved to canonical ids where possible. Many prospects are high
schoolers, who have no college program to resolve to -- those rows keep
``team_id`` empty and are flagged ``is_college``.
"""

import argparse
import csv
import os
import re

from ncaa_bbStats._paths import data_path
from ncaa_bbStats.team_registry import resolve_team

DEFAULT_YEARS = list(range(2021, 2027))

OUTPUT_COLUMNS = [
    "year", "rank", "name", "position", "school", "team_id", "is_college",
    "age", "bats", "throws", "current_level",
]

# A school string that looks like a high school rather than a college program.
_HIGH_SCHOOL = re.compile(
    r"\b(hs|high school|academy|prep|preparatory)\b|\([A-Z]{2}\)\s*$",
    re.IGNORECASE,
)


def _int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def convert_row(row: dict, season: int) -> dict:
    """Convert one prospect row, resolving the school where it is a college."""
    school = (row.get("school") or "").strip()
    team_id = resolve_team(school) if school else None

    # A two-letter state suffix, as in "Stillwater (OK)", marks a high school.
    looks_like_high_school = bool(_HIGH_SCHOOL.search(school))

    return {
        "year": season,
        "rank": _int(row.get("rank")),
        "name": (row.get("name") or "").strip(),
        "position": (row.get("position") or "").strip(),
        "school": school,
        "team_id": team_id or "",
        "is_college": bool(team_id) and not looks_like_high_school,
        "age": _int(row.get("age")),
        "bats": (row.get("bats") or "").strip(),
        "throws": (row.get("throws") or "").strip(),
        "current_level": (row.get("current_level") or "").strip(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-dir", required=True)
    parser.add_argument("--years", type=int, nargs="+", default=DEFAULT_YEARS)
    parser.add_argument("--out", default=data_path("prospects"))
    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    total = 0

    for season in args.years:
        matches = [
            os.path.join(args.from_dir, name)
            for name in sorted(os.listdir(args.from_dir))
            if name.endswith(".csv") and str(season) in re.findall(r"\d{4}", name)
        ]
        if not matches:
            print(f"  {season}: no source file, skipping")
            continue

        with open(matches[0], newline="", encoding="utf-8-sig") as f:
            rows = [convert_row(r, season) for r in csv.DictReader(f)]

        path = os.path.join(args.out, f"{season}.csv")
        with open(path, "w", newline="\n", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS,
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

        college = sum(1 for r in rows if r["is_college"])
        print(f"  {season}: {len(rows):3d} prospects ({college:3d} college) "
              f"-> {os.path.relpath(path)}")
        total += len(rows)

    print(f"\n{total} prospects cached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
