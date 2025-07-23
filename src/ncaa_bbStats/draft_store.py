import os
import json
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "mlb_draft_cache"))
os.makedirs(BASE_DIR, exist_ok=True)

COLUMN_NAMES = ["Round", "Pick", "Phase", "Player Name", "Drafted By", "POS", "Drafted From"]

def parse_mlb_draft(year: int) -> list[dict]:
    if not (1965 <= year <= 2025):
        raise ValueError("Year must be between 1965 and 2025")

    url = f"https://www.baseball-almanac.com/draft/baseball-draft.php?yr={year}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if not table:
        raise ValueError(f"No draft table found for year {year}.")

    rows = table.find_all("tr")
    data_rows = rows[2:-2]  # Skip headers and malformed closing row

    draft_picks = []
    for row in data_rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) != 7:
            continue  # Skip malformed rows
        record = dict(zip(COLUMN_NAMES, cols))
        record["Year"] = year
        draft_picks.append(record)

    return draft_picks


def save_yearly_drafts(start_year=1965, end_year=2025):
    for year in range(start_year, end_year + 1):
        print(f"Processing MLB Draft for {year}...")
        try:
            picks = parse_mlb_draft(year)
            output_path = os.path.join(BASE_DIR, f"{year}.json")
            with open(output_path, "w") as f:
                json.dump(picks, f, indent=2)
            print(f"Saved {len(picks)} picks to {output_path}")
        except Exception as e:
            print(f"Skipped {year} due to error: {e}")


def save_combined_draft(start_year=1965, end_year=2025, output_file="all_drafts.json"):
    all_drafts = []
    for year in range(start_year, end_year + 1):
        print(f"Aggregating draft for {year}...")
        try:
            picks = parse_mlb_draft(year)
            all_drafts.extend(picks)
        except Exception as e:
            print(f"Failed to include {year}: {e}")

    combined_path = os.path.join(BASE_DIR, output_file)
    with open(combined_path, "w") as f:
        json.dump(all_drafts, f, indent=2)
    print(f"Total aggregated picks: {len(all_drafts)} — saved to {combined_path}")
