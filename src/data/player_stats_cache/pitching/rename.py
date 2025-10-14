import csv
import os

# File paths (edit if needed)
script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
data_file = os.path.join(script_dir, "pitching_qualified.csv")  # Main CSV (contains 'team' column)
teams_file = os.path.join(script_dir, "unique_teams.csv")  # Reference CSV (Acronym, Full Name)
output_file = os.path.join(script_dir, "merged.csv")  # Output file

# Load team name mappings
team_map = {}
with open(teams_file, newline='', encoding='utf-8') as tf:
    reader = csv.DictReader(tf)
    for row in reader:
        acronym = row['Acronym'].strip()
        full_name = row['Full Name'].strip()
        team_map[acronym] = full_name

# Process data.csv
with open(data_file, newline='', encoding='utf-8') as df:
    reader = csv.DictReader(df)
    fieldnames = reader.fieldnames

    # Find where 'team' column is
    team_index = fieldnames.index('team')

    # Insert 'team name' right after it
    new_fieldnames = fieldnames[:team_index+1] + ['team name'] + fieldnames[team_index+1:]

    with open(output_file, 'w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=new_fieldnames)
        writer.writeheader()

        for row in reader:
            acronym = row['team'].strip()
            row['team name'] = team_map.get(acronym, '')
            # Reorder columns correctly
            ordered_row = {k: row.get(k, '') for k in new_fieldnames}
            writer.writerow(ordered_row)

print(f"✅ Done! Created '{output_file}' with team names beside 'team'.")
