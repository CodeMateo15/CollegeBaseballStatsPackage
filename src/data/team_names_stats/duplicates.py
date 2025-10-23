import pandas as pd

# === Load standardized CSV ===
df = pd.read_csv("all_div_teams_standardized.csv")

# === Filter for Division 1 only ===
div1_df = df[df["division"] == 1]

# === Find duplicates (case-insensitive) ===
duplicates = (
    div1_df["team_name"]
    .str.lower()
    .value_counts()
    .loc[lambda x: x > 1]
    .index.tolist()
)

if duplicates:
    print("\n⚠️  Duplicate team names found in all_div_teams_standardized.csv:\n")
    for dup in duplicates:
        dup_rows = div1_df[div1_df["team_name"].str.lower() == dup]
        print(dup_rows.to_string(index=False))
        print("-" * 60)
    print(f"\nTotal duplicate groups found: {len(duplicates)}")
else:
    print("✅ No duplicate team names found.")
