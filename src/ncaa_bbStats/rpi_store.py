"""Cache Warren Nolan RPI, strength of schedule, and quadrant records.

Run as a script; importing this module has no side effects.

    python -m ncaa_bbStats.rpi_store --from-dir path/to/ncaa_rpiYears

RPI is a third-party computation, not an official NCAA statistic, and Warren
Nolan publishes it for Division I only from 2021. Team names are resolved to
canonical ids through :mod:`ncaa_bbStats.team_registry`, so the rows join
against everything else in the package.

The source files store each record twice -- once as ``"20-10"`` and once split
into wins and losses. Only the split form is kept, plus a win percentage
computed here, since parsing the string form at read time is pure overhead.
"""

import argparse
import csv
import os
import re

from ncaa_bbStats._paths import data_path
from ncaa_bbStats.team_registry import resolve_team

DEFAULT_YEARS = list(range(2021, 2027))

# Source column stem -> output prefix. Each has _Wins and _Losses companions.
RECORD_FIELDS = {
    "Conference_Record": "conference",
    "Overall_Record": "overall",
    "NC_Rec": "nonconference",
    "H": "home",
    "R": "road",
    "N": "neutral",
    "Q1": "q1",
    "Q2": "q2",
    "Q3": "q3",
    "Q4": "q4",
}

SCALAR_FIELDS = {
    "Rank": "rpi_rank",
    "SOS": "sos_rank",
    "NC_RPI": "nonconference_rpi_rank",
    "NC_SOS": "nonconference_sos_rank",
}

OUTPUT_COLUMNS = (
    ["team_id", "team_name", "season", "conference"]
    + list(SCALAR_FIELDS.values())
    + [f"{prefix}_{suffix}"
       for prefix in RECORD_FIELDS.values()
       for suffix in ("wins", "losses", "win_pct")]
)


def _int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _win_pct(wins, losses):
    """Winning percentage, or None when no games were played."""
    if wins is None or losses is None:
        return None
    total = wins + losses
    if total == 0:
        return None
    return round(wins / total, 4)


def convert_row(row: dict, season: int) -> dict:
    """Convert one source row to the cached shape.

    Args:
        row (dict): A row from a Warren Nolan RPI export.
        season (int): The season the file covers.

    Returns:
        dict: The converted row. ``team_id`` is None if the name did not resolve.
    """
    name = (row.get("Team") or "").strip()
    # Resolved by name alone, without season or division constraints. Warren
    # Nolan covers Division I by definition, but a program can appear here with
    # no matching NCAA record for that exact season: reclassifying schools
    # (Bellarmine, Tarleton State, Stonehill, Le Moyne) show up on the RPI board
    # while the NCAA cache still has them in Division II, and the 2021 Ivy
    # League has an RPI row but no season, having cancelled play. Names are
    # unambiguous across the registry, so nothing is gained by constraining.
    out = {
        "team_id": resolve_team(name),
        "team_name": name,
        "season": season,
        "conference": (row.get("Conference") or "").strip(),
    }
    for source, target in SCALAR_FIELDS.items():
        out[target] = _int(row.get(source))

    for source, prefix in RECORD_FIELDS.items():
        wins = _int(row.get(f"{source}_Wins"))
        losses = _int(row.get(f"{source}_Losses"))
        out[f"{prefix}_wins"] = wins
        out[f"{prefix}_losses"] = losses
        out[f"{prefix}_win_pct"] = _win_pct(wins, losses)
    return out


def convert_file(path: str, season: int):
    """Convert one season file. Returns (rows, unresolved_names)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        source_rows = list(csv.DictReader(f))

    rows, unresolved = [], []
    for source_row in source_rows:
        row = convert_row(source_row, season)
        if row["team_id"] is None:
            unresolved.append(row["team_name"])
        rows.append(row)
    return rows, unresolved


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-dir", required=True,
                        help="Directory of ncaa_rpi_{year}.csv files.")
    parser.add_argument("--years", type=int, nargs="+", default=DEFAULT_YEARS)
    parser.add_argument("--out", default=data_path("rpi"))
    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    all_unresolved = {}
    total = 0

    for season in args.years:
        # Match the year as a standalone 4-digit run. A \b boundary does not
        # work here: underscore is a word character, so "_2021" has no boundary
        # before the digits.
        matches = [
            os.path.join(args.from_dir, name)
            for name in sorted(os.listdir(args.from_dir))
            if name.endswith(".csv")
            and str(season) in re.findall(r"\d{4}", name)
        ]
        if not matches:
            print(f"  {season}: no source file, skipping")
            continue

        rows, unresolved = convert_file(matches[0], season)
        if unresolved:
            all_unresolved[season] = unresolved

        path = os.path.join(args.out, f"{season}.csv")
        with open(path, "w", newline="\n", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS,
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"  {season}: {len(rows):3d} teams -> {os.path.relpath(path)}")
        total += len(rows)

    if all_unresolved:
        print("\nUNRESOLVED team names -- these rows cannot be joined:")
        for season, names in sorted(all_unresolved.items()):
            print(f"  {season}: {sorted(set(names))}")
        print("\nAdd them to tools/team_aliases_manual.csv and rebuild the "
              "registry. Refusing to leave a silent join failure.")
        return 1

    print(f"\n{total} team-seasons cached, all resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
