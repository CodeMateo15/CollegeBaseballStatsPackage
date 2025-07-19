import requests
from bs4 import BeautifulSoup
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://d1baseball.com/',
    'DNT': '1'
}

def fetch_player_stats(stat_type='batting', url=None):
    assert stat_type in ['batting', 'pitching'], "stat_type must be 'batting' or 'pitching'"

    session = requests.Session()

    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        # short pause to be respectful
        time.sleep(1)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')

        if not tables:
            print("No tables found on the page")
            return []

        target_table = None

        for table in tables:
            thead = table.find('thead')
            if not thead:
                continue
            headers = [th.text.strip() for th in thead.find_all('th')]
            if stat_type == 'pitching' and any(col in headers for col in ['ERA', 'W', 'SO']):
                target_table = table
                break
            elif stat_type == 'batting' and any(col in headers for col in ['SLG', 'PA', 'HR']):
                target_table = table
                break

        if not target_table:
            print(f"No {stat_type} table found based on header matching")
            return []

        tbody = target_table.find('tbody')
        if not tbody:
            print("No table body found in target table")
            return []

        season = extract_season(url)
        players = []
        for row in tbody.find_all('tr'):
            cols = [td.text.strip() for td in row.find_all('td')]
            # Pad or truncate columns to match headers
            if len(cols) < len(headers):
                cols += [''] * (len(headers) - len(cols))
            elif len(cols) > len(headers):
                cols = cols[:len(headers)]
            player_data = dict(zip(headers, cols))
            player_data.pop('Qual.', None)
            player_data['Season'] = str(season)
            players.append(player_data)

        print(f"Fetched {len(players)} {stat_type} players.")
        return players

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def extract_season(seasonURL):
    import re
    match = re.search(r'season=(\d+)', seasonURL)
    return int(match.group(1)) if match else None
