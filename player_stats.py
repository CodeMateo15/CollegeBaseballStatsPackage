import requests
from bs4 import BeautifulSoup
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://d1baseball.com/',
    'DNT': '1'
}

BASE_URL = 'https://d1baseball.com/statistics/'


def fetch_player_stats(stat_type='batting'):
    assert stat_type in ['batting', 'pitching'], "stat_type must be 'batting' or 'pitching'"

    url = f'{BASE_URL}'
    session = requests.Session()

    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        time.sleep(1)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')

        if not table:
            print("No table found")
            return []

        headers = [th.text.strip() for th in table.find('thead').find_all('th')]
        players = []

        for row in table.find('tbody').find_all('tr'):
            cols = [td.text.strip() for td in row.find_all('td')]
            if len(cols) != len(headers):
                continue
            player_data = dict(zip(headers, cols))
            players.append(player_data)

        print(f"Fetched {len(players)} {stat_type} players.")
        return players

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


