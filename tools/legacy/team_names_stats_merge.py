import sys
import pandas as pd

def main(old_path="all_div_teams.csv", new_path="all_div_teams_standardized.csv", out_path="team_name_mapping.csv"):
    # Read CSVs (treat team_id as string to preserve leading zeros if any)
    old = pd.read_csv(old_path, dtype={"team_id": str})
    new = pd.read_csv(new_path, dtype={"team_id": str})

    # Keep relevant columns and dedupe by team_id+division
    old = old[["team_id", "division", "team_name"]].drop_duplicates(subset=["team_id", "division"]).rename(columns={"team_name": "team_old"})
    new = new[["team_id", "division", "team_name"]].drop_duplicates(subset=["team_id", "division"]).rename(columns={"team_name": "team_new"})

    # Outer merge so every team_id+division from either file appears; will contain both team_old and team_new columns
    mapped = pd.merge(old, new, on=["team_id", "division"], how="outer")

    # Optional: ensure columns exist even if missing from one file
    if "team_old" not in mapped:
        mapped["team_old"] = pd.NA
    if "team_new" not in mapped:
        mapped["team_new"] = pd.NA

    # Normalize empty strings / whitespace-only to pd.NA so counts are accurate
    mapped["team_old"] = mapped["team_old"].replace(r"^\s*$", pd.NA, regex=True)
    mapped["team_new"] = mapped["team_new"].replace(r"^\s*$", pd.NA, regex=True)

    # Natural (numeric) sort by team_id then division:
    # Create a temporary numeric key for proper ordering (coerce errors to NaN -> placed last)
    mapped["_team_id_num"] = pd.to_numeric(mapped["team_id"], errors="coerce")
    mapped = mapped.sort_values(by=["_team_id_num", "division", "team_old", "team_new"], na_position="last").reset_index(drop=True)
    mapped = mapped.drop(columns=["_team_id_num"])

    mapped.to_csv(out_path, index=False)
    print(f"Wrote {len(mapped)} rows to {out_path}")

    # Accurate counts: consider pd.NA (and not-empty strings) as present
    has_old = mapped["team_old"].notna()
    has_new = mapped["team_new"].notna()

    both_mask = has_old & has_new
    total_both = int(both_mask.sum())

    # Count how many of the 'both' rows have identical names (case-insensitive, trimmed)
    identical = mapped.loc[both_mask & (
        mapped["team_old"].astype(str).str.strip().str.lower()
        == mapped["team_new"].astype(str).str.strip().str.lower()
    )].shape[0]

    only_old = int((has_old & ~has_new).sum())
    only_new = int((has_new & ~has_old).sum())

    print(f"Rows with both names: {total_both} (identical: {identical}); only_old: {only_old}; only_new: {only_new}")

if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)