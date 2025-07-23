import os
import json
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "mlb_draft_cache"))
os.makedirs(BASE_DIR, exist_ok=True)

COLUMN_NAMES = ["Round", "Pick", "Phase", "Player Name", "Drafted By", "POS", "Drafted From"]

def parse_mlb_draft(year: int) -> list[dict]:
    """
    Parses MLB Draft data for a given year from Baseball Almanac.

    Args:
        year (int): The year of the MLB draft to parse. Must be between 1965 and 2025.

    Returns:
        list[dict]: A list of dictionaries, each representing a single draft pick
                    with keys: "Round", "Pick", "Phase", "Player Name",
                    "Drafted By", "POS", "Drafted From", and "Year".

    Raises:
        ValueError: If the year is out of the allowed range or the draft table is not found.
        requests.exceptions.RequestException: If there is an issue fetching the webpage.
    """

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
    """
    Parses and saves MLB Draft data for each year in the given range to individual JSON files.

    Args:
        start_year (int, optional): The first year to parse. Defaults to 1965.
        end_year (int, optional): The last year to parse. Defaults to 2025.

    Side Effects:
        Creates a directory `mlb_draft_cache` (if not already present) in the `data` folder.
        Writes one JSON file per year with draft pick data.

    Notes:
        If a year's data cannot be parsed, the year is skipped and an error message is printed.
    """

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
    """
    Parses MLB Draft data for a range of years and saves all draft picks to a single JSON file.

    Args:
        start_year (int, optional): The first year to include. Defaults to 1965.
        end_year (int, optional): The last year to include. Defaults to 2025.
        output_file (str, optional): The name of the combined JSON output file. Defaults to "all_drafts.json".

    Side Effects:
        Creates a directory `mlb_draft_cache` (if not already present) in the `data` folder.
        Writes a single JSON file containing all aggregated draft pick data.

    Notes:
        If a year's data cannot be parsed, that year's picks are excluded and an error message is printed.
    """

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
