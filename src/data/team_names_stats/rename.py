import pandas as pd
from difflib import get_close_matches

# === Load CSVs ===
unique_df = pd.read_csv("unique_teams.csv")
all_div_df = pd.read_csv("all_div_teams.csv")

unique_names = unique_df["Full Name"].tolist()

# === Matching Function ===
def find_best_match(team_name):
    # 1️⃣ Try substring match
    for full_name in unique_names:
        if team_name.lower() in full_name.lower():
            return full_name
    # 2️⃣ Fallback to fuzzy match
    matches = get_close_matches(team_name, unique_names, n=1, cutoff=0.5)
    if matches:
        return matches[0]
    return team_name

def standardize_team_name(row):
    if row["division"] != 1:
        return row["team_name"]
    return find_best_match(row["team_name"])

# === Apply Standardization ===
all_div_df["team_name"] = all_div_df.apply(standardize_team_name, axis=1)

# === Duplicate Check ===
duplicates = (
    all_div_df["team_name"]
    .str.lower()
    .value_counts()
    .loc[lambda x: x > 1]
    .index.tolist()
)

if duplicates:
    print("\n⚠️  Duplicate standardized team names found:\n")
    for dup in duplicates:
        dup_rows = all_div_df[all_div_df["team_name"].str.lower() == dup]
        print(dup_rows.to_string(index=False))
        print("-" * 60)
else:
    print("✅ No duplicate team names found.")

# === Unused Unique Teams Check ===
# Only look at Division 1 names, since those are standardized
used_names = set(
    all_div_df.loc[all_div_df["division"] == 1, "team_name"].unique()
)

unused = [name for name in unique_names if name not in used_names]

if unused:
    print("\n⚠️  Unique teams NOT used in any Division 1 match:\n")
    for name in unused:
        print("-", name)
else:
    print("\n✅ All unique teams were matched to at least one Division 1 team.")

# === Save Result ===
all_div_df.to_csv("all_div_teams_standardized.csv", index=False)
print("\n✅ Standardized names saved to all_div_teams_standardized.csv")
