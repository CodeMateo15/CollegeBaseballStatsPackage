import os
import json
import csv
import re

def extract_unique_teams_stats(base_dir: str, output_csv_name: str):
    seen_teams = set()
    team_records = []

    for division in range(1, 4):
        for year in range(2002, 2026):
            file_path = os.path.join(
                os.path.dirname(__file__),
                "..", base_dir, f"div{division}", f"{year}.json"
            )
            file_path = os.path.abspath(file_path)

            if not os.path.isfile(file_path):
                continue

            with open(file_path, "r") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON file: {file_path}")
                    continue

                for team_name in stats.keys():
                    if not team_name:
                        continue

                    # Remove anything in parentheses, e.g., "Adelphi (NE10)" -> "Adelphi"
                    cleaned_name = re.sub(r"\s*\(.*?\)", "", team_name).strip()

                    key = (cleaned_name, division)
                    if key not in seen_teams:
                        seen_teams.add(key)
                        team_records.append(key)

    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "team_names_stats")
    os.makedirs(output_dir, exist_ok=True)

    output_csv_path = os.path.join(output_dir, output_csv_name)

    # Write to CSV
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['team_id', 'team_name', 'division'])
        for idx, (team, division) in enumerate(sorted(team_records), start=1):
            writer.writerow([idx, team, division])


def extract_unique_mlb_teams(base_dir: str, drafted_by_csv: str, drafted_from_csv: str):
    drafted_by_teams = set()
    drafted_from_teams = set()

    cache_dir = os.path.join(os.path.dirname(__file__), "..", base_dir)
    cache_dir = os.path.abspath(cache_dir)

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
                    # Remove anything in parentheses for schools
                    cleaned_frm = re.sub(r"\s*\(.*?\)", "", frm).strip()
                    if cleaned_frm:
                        drafted_from_teams.add(cleaned_frm)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "mlb_team_names")
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

# Usage
extract_unique_mlb_teams('data/mlb_draft_cache', 'drafted_by_teams.csv', 'drafted_from_schools.csv')

# Usage
extract_unique_teams_stats('data/team_stats_cache', 'all_div_teams.csv')
