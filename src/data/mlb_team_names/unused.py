import pandas as pd
import re
import sys

# === File paths ===
unique_path = "unique_teams.csv"           # Acronym, Full Name
standard_path = "drafted_from_schools.csv" # school_id, school_name

if len(sys.argv) > 1:
    unique_path = sys.argv[1]
if len(sys.argv) > 2:
    standard_path = sys.argv[2]

# === Load CSVs ===
unique_df = pd.read_csv(unique_path)
standard_df = pd.read_csv(standard_path)

# === Normalization function ===
def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s]", "", name)  # remove punctuation
    name = re.sub(r"\s+", " ", name)         # collapse extra spaces
    return name

# === Normalize all names ===
unique_df["norm"] = unique_df["Full Name"].apply(normalize_name)
standard_df["norm"] = standard_df["school_name"].apply(normalize_name)

unique_names = set(unique_df["norm"])
used_names = set(standard_df["norm"])

# === Find unused and duplicates ===
unused = [row["Full Name"] for _, row in unique_df.iterrows() if row["norm"] not in used_names]

used_multiple = (
    standard_df["norm"]
    .value_counts()
    .loc[lambda x: x > 1]
    .index.tolist()
)

# === Output ===
print("\n🔍 Checking standardized teams coverage...\n")

if not unused:
    print("✅ All unique teams are represented in the standardized dataset")
else:
    print(f"⚠️  {len(unused)} unique teams NOT matched:\n")
    for name in unused:
        print("-", name)
    print("-" * 60)

if used_multiple:
    print(f"\n⚠️  {len(used_multiple)} entries appear multiple times in the standardized dataset:\n")
    for dup in used_multiple:
        dup_rows = standard_df[standard_df["norm"] == dup]
        print(dup_rows.to_string(index=False))
        print("-" * 60)
else:
    print("✅ No entry appears multiple times.")

print("\nCheck complete.")
