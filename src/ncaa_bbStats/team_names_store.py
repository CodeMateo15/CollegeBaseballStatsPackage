"""Extract the distinct team and school names appearing in the cached datasets.

Run as a script; importing this module has no side effects.

    python -m ncaa_bbStats.team_names_store
"""

import os
import json
import csv

from ncaa_bbStats._normalize import strip_all_parens, strip_league
from ncaa_bbStats._paths import data_path, load_team_stats

# Team-stat caches exist for these seasons. Kept in sync with team_store.py.
FIRST_SEASON = 2002
LAST_SEASON = 2026


def extract_unique_teams_stats(base_dir: str, output_csv_name: str):
    """Write the distinct (team, division) pairs found in the team-stats cache.

    Args:
        base_dir (str): Unused, retained for backward compatibility. The cache is
            always read through :func:`ncaa_bbStats._paths.load_team_stats`.
        output_csv_name (str): File name to write under data/team_names_stats.
    """
    seen_teams = set()
    team_records = []

    for division in range(1, 4):
        for year in range(FIRST_SEASON, LAST_SEASON + 1):
            try:
                # load_team_stats drops the "division" bookkeeping key, which
                # would otherwise be recorded here as a team named "division".
                stats = load_team_stats(year, division)
            except FileNotFoundError:
                continue
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON for division {division}, {year}")
                continue

            for team_name in stats.keys():
                if not team_name:
                    continue

                # Drop only the league suffix: "Adelphi (NE10)" -> "Adelphi",
                # but "Miami (OH) (MAC)" -> "Miami (OH)". Removing every
                # parenthesised group instead collapsed 134 labels, merging
                # genuinely distinct schools (Anderson IN/SC, Augustana IL/SD,
                # Centenary LA/NJ, Miami OH/FL) into a single row each.
                cleaned_name = strip_league(team_name)
                if not cleaned_name:
                    continue

                key = (cleaned_name, division)
                if key not in seen_teams:
                    seen_teams.add(key)
                    team_records.append(key)

    # Create output directory if it doesn't exist
    output_dir = data_path("team_names_stats")
    os.makedirs(output_dir, exist_ok=True)

    output_csv_path = os.path.join(output_dir, output_csv_name)

    # Write to CSV
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['team_id', 'team_name', 'division'])
        for idx, (team, division) in enumerate(sorted(team_records), start=1):
            writer.writerow([idx, team, division])


def extract_unique_mlb_teams(base_dir: str, drafted_by_csv: str, drafted_from_csv: str):
    """Write the distinct drafting clubs and drafted-from schools in the draft cache.

    Args:
        base_dir (str): Data-relative directory holding the draft JSON files,
            e.g. ``"mlb_draft_cache"``.
        drafted_by_csv (str): File name for the MLB club list.
        drafted_from_csv (str): File name for the school list.
    """
    drafted_by_teams = set()
    drafted_from_teams = set()

    cache_dir = data_path(os.path.basename(base_dir.rstrip("/")))

    for fname in os.listdir(cache_dir):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(cache_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON file: {fpath}")
                continue
            for entry in data:
                by = entry.get("Drafted By", "").strip()
                frm = entry.get("Drafted From", "").strip()
                # Clean up: skip empty or dash
                if by and by != "-":
                    drafted_by_teams.add(by)
                if frm and frm != "-":
                    # Baseball Almanac appends a location, e.g.
                    # "Fort Cobb-Broxton High School (Fort Cobb, OK)". Unlike
                    # NCAA team labels, every parenthesised group here is
                    # location noise rather than part of the school's identity.
                    cleaned_frm = strip_all_parens(frm)
                    if cleaned_frm:
                        drafted_from_teams.add(cleaned_frm)

    output_dir = data_path("mlb_team_names")
    os.makedirs(output_dir, exist_ok=True)

    # Write Drafted By teams
    with open(os.path.join(output_dir, drafted_by_csv), "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["team_id", "team_name"])
        for idx, team in enumerate(sorted(drafted_by_teams), 1):
            writer.writerow([idx, team])

    # Write Drafted From teams/schools
    with open(os.path.join(output_dir, drafted_from_csv), "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["school_id", "school_name"])
        for idx, school in enumerate(sorted(drafted_from_teams), 1):
            # Remove any leading/trailing quotes
            school = school.strip('"')
            writer.writerow([idx, school])

def main():
    """Regenerate every name-extraction CSV from the current caches."""
    extract_unique_mlb_teams(
        "mlb_draft_cache", "drafted_by_teams.csv", "drafted_from_schools.csv"
    )
    print("Wrote data/mlb_team_names/{drafted_by_teams,drafted_from_schools}.csv")

    extract_unique_teams_stats("team_stats_cache", "all_div_teams.csv")
    print("Wrote data/team_names_stats/all_div_teams.csv")


# Importing this module used to run both extractors, silently rewriting CSVs on
# disk as a side effect of `import`. They are only invoked as a script now.
if __name__ == "__main__":
    main()
