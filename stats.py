import requests
from bs4 import BeautifulSoup
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.ncaa.org/',
    'DNT': '1'
}

def fetch_ncaa_table(url, parse_row_fn):
    session = requests.Session()
    max_retries = 3

    for _ in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            time.sleep(5)  # Respectful delay

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': 'rankings_table'})

            if not table:
                return {}

            results = {}
            for row in table.select('tbody tr'):
                cols = row.find_all('td')
                try:
                    parsed = parse_row_fn(cols)
                    if parsed:
                        key, data = parsed
                        results[key] = data
                except Exception as e:
                    print(f"Skipping row: {str(e)}")
                    continue

            return results

        except requests.exceptions.RequestException as e:
            print(f"Attempt failed: {e}")
            time.sleep(10)

    return {}

def parse_base_on_balls_row(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'games': int(cols[2].text.strip()),
            'wins': wins,
            'losses': losses,
            'base_on_balls': int(cols[4].text.strip())
        }
    )

def parse_batting_average_row(cols):
    if len(cols) < 7:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'games': int(cols[2].text.strip()),
            'wins': wins,
            'losses': losses,
            'at-bat': int(cols[4].text.strip().replace(',', '')),
            'hits': int(cols[5].text.strip()),
            'batting_average': float(cols[6].text.strip())
        }
    )

def parse_double_plays_per_game(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'games': int(cols[2].text.strip()),
            'wins': wins,
            'losses': losses,
            'double_play': int(cols[4].text.strip()),
            'double_play_per_game': float(cols[5].text.strip())
        }
    )

def parse_double_plays(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'games': int(cols[2].text.strip()),
            'wins': wins,
            'losses': losses,
            'double_play': int(cols[4].text.strip())
        }
    )
#27 more
def extract_team_league(team_league_str):
    if '(' in team_league_str and ')' in team_league_str:
        team, league = team_league_str.rsplit('(', 1)
        return team.strip(), league.strip(')')
    return team_league_str.strip(), ''

def combine_team_stats(*stats_dicts):
    combined = {}

    for stat_dict in stats_dicts:
        for key, value in stat_dict.items():
            if key not in combined:
                combined[key] = {}

            # Exclude the 'rank' key from each stat entry
            filtered_value = {k: v for k, v in value.items() if k != 'rank'}
            combined[key].update(filtered_value)

    return combined


# Edit these to include input on academic year and division
def base_on_balls():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=496.0"
    return fetch_ncaa_table(url, parse_base_on_balls_row)

def batting_average():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=210.0"
    return fetch_ncaa_table(url, parse_batting_average_row)

def double_plays_per_game():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=328.0"
    return fetch_ncaa_table(url, parse_double_plays_per_game)

def double_plays():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=501.0"
    return fetch_ncaa_table(url, parse_double_plays)