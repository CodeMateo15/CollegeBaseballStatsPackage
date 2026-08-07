import pandas as pd
import re
import sys

# === File paths ===
unique_path = "unique_teams.csv"
standard_path = "all_div_teams_standardized.csv"

if len(sys.argv) > 1:
    unique_path = sys.argv[1]
if len(sys.argv) > 2:
    standard_path = sys.argv[2]

# === Load CSVs ===
unique_df = pd.read_csv(unique_path)
standard_df = pd.read_csv(standard_path)

# === Filter to Division 1 ===
div1_df = standard_df[standard_df["division"] == 1]

# === Normalization function ===
def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s]", "", name)   # remove punctuation
    name = re.sub(r"\s+", " ", name)          # collapse extra spaces
    return name

# === Normalize all names ===
unique_df["norm"] = unique_df["Full Name"].apply(normalize_name)
div1_df["norm"] = div1_df["team_name"].apply(normalize_name)

unique_names = set(unique_df["norm"])
used_names = set(div1_df["norm"])

# === Find unused and duplicate teams ===
unused = [row["Full Name"] for _, row in unique_df.iterrows() if row["norm"] not in used_names]

used_multiple = (
    div1_df["norm"]
    .value_counts()
    .loc[lambda x: x > 1]
    .index.tolist()
)

# === Output ===
print("\n🔍 Checking Division 1 standardization coverage...\n")

if not unused:
    print("✅ All unique Division 1 teams are represented in all_div_teams_standardized.csv")
else:
    print(f"⚠️  {len(unused)} unique teams NOT matched in Division 1:\n")
    for name in unused:
        print("-", name)
    print("-" * 60)

if used_multiple:
    print(f"\n⚠️  {len(used_multiple)} teams appear multiple times in Division 1:\n")
    for dup in used_multiple:
        dup_rows = div1_df[div1_df["norm"] == dup]
        print(dup_rows.to_string(index=False))
        print("-" * 60)
else:
    print("✅ No team appears multiple times in Division 1.")

print("\nCheck complete.")
