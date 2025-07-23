import requests
from bs4 import BeautifulSoup
import time
import numpy as np

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.ncaa.org/',
    'DNT': '1'
}

def fetch_ncaa_table(url, parse_row_fn):
    session = requests.Session()
    max_retries = 1

    for _ in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            time.sleep(1)

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
                    # About 5 rows are skipped each time due to the format of the NCAA page
                    # print(f"Skipping row: {str(e)}")
                    continue

            print(f"Finished fetching {parse_row_fn.__name__}")
            return results

        except requests.exceptions.RequestException as e:
            print(f"Attempt failed: {e}")
            time.sleep(5)

    return {}

def parse_base_on_balls_row(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'BB (Batting)': int(cols[4].text.strip())
        }
    )

def parse_batting_average(cols):
    if len(cols) < 7:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'AB': int(cols[4].text.strip().replace(',', '')),
            'H': int(cols[5].text.strip()),
            'BA': float(cols[6].text.strip())
        }
    )

def parse_double_plays_per_game(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'DP': int(cols[4].text.strip()),
            'DPPG': float(cols[5].text.strip())
        }
    )

def parse_double_plays(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'DP': int(cols[4].text.strip())
        }
    )

def parse_doubles(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            '2B': int(cols[4].text.strip())
        }
    )

def parse_doubles_per_game(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            '2B': int(cols[4].text.strip()),
            '2BPG': float(cols[5].text.strip())
        }
    )

def parse_earned_run_average(cols):
    if len(cols) < 8:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'IP': float(cols[4].text.strip()),
            'R (Pitching)': int(cols[5].text.strip()),
            'ER': int(cols[6].text.strip()),
            'ERA': float(cols[7].text.strip())
        }
    )

def parse_fielding_percentage(cols):
    if len(cols) < 8:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'PO': int(cols[4].text.strip().replace(',', '')),
            'A': int(cols[5].text.strip()),
            'E': int(cols[6].text.strip()),
            'FPCT': float(cols[7].text.strip())
        }
    )

def parse_hit_batters(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'IP': float(cols[4].text.strip()),
            'HB': int(cols[5].text.strip())
        }
    )

def parse_hit_by_pitch(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'HBP': float(cols[4].text.strip())
        }
    )

def parse_hits(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'AB': int(cols[4].text.strip().replace(',', '')),
            'H': int(cols[5].text.strip())
        }
    )

def parse_hits_allowed_per_nine_innings(cols):
    if len(cols) < 7:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'IP': float(cols[4].text.strip()),
            'HA': int(cols[5].text.strip()),
            'HAPG': float(cols[6].text.strip())
        }
    )

def parse_home_runs(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'HR': int(cols[4].text.strip())
        }
    )

def parse_home_runs_per_game(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'HR': int(cols[4].text.strip()),
            'HRPG': float(cols[5].text.strip())
        }
    )

def parse_on_base_percentage(cols):
    if len(cols) < 11:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'AB': int(cols[4].text.strip().replace(',', '')),
            'H': int(cols[5].text.strip()),
            'BB (Batting)': int(cols[6].text.strip()),
            'HBP': int(cols[7].text.strip()),
            'SF': int(cols[8].text.strip()),
            'SH': int(cols[9].text.strip()),
            'OBP': float(cols[10].text.strip())
        }
    )

def parse_runs(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'R (Batting)': int(cols[4].text.strip())
        }
    )

def parse_sacrifice_bunts(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'SH': int(cols[4].text.strip())
        }
    )

def parse_sacrifice_flies(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'SF': int(cols[4].text.strip())
        }
    )

def parse_scoring(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'R (Batting)': int(cols[4].text.strip()),
            'RPG': float(cols[5].text.strip())
        }
    )

def parse_shutouts(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'SHO': int(cols[4].text.strip())
        }
    )

def parse_slugging_percentage(cols):
    if len(cols) < 7:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'AB': int(cols[4].text.strip().replace(',', '')),
            'TB': int(cols[5].text.strip().replace(',', '')),
            'SLG': float(cols[6].text.strip())
        }
    )

def parse_stolen_bases(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'SB': int(cols[4].text.strip()),
            'CS': int(cols[5].text.strip())
        }
    )

def parse_stolen_bases_per_game(cols):
    if len(cols) < 7:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'SB': int(cols[4].text.strip()),
            'CS': int(cols[5].text.strip()),
            'SBPG': float(cols[6].text.strip())
        }
    )

def parse_strikeout_to_walk_ratio(cols):
    if len(cols) < 8:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'IP': float(cols[4].text.strip()),
            'SO': int(cols[5].text.strip()),
            'BB (Pitching)': int(cols[6].text.strip()),
            'K/BB': float(cols[7].text.strip())
        }
    )

def parse_strikeouts_per_nine_innings(cols):
    if len(cols) < 7:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'IP': float(cols[4].text.strip()),
            'SO': int(cols[5].text.strip()),
            'K/9': float(cols[6].text.strip())
        }
    )

def parse_triple_plays(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'TP': int(cols[4].text.strip())
        }
    )

def parse_triples(cols):
    if len(cols) < 5:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            '3B': int(cols[4].text.strip())
        }
    )

def parse_triples_per_game(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            '3B': int(cols[4].text.strip()),
            '3BPG': float(cols[5].text.strip())
        }
    )

def parse_whip(cols):
    if len(cols) < 7:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'W': wins,
            'L': losses,
            'T': tie,
            'IP': float(cols[2].text.strip()),
            'BB (Pitching)': int(cols[4].text.strip()),
            'HA': int(cols[5].text.strip()),
            'WHIP': float(cols[6].text.strip())
        }
    )

def parse_winning_percentage(cols):
    if len(cols) < 6:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'W': int(cols[2].text.strip()),
            'L': int(cols[3].text.strip()),
            'T': int(cols[4].text.strip()),
            'WPCT': float(cols[5].text.strip())
        }
    )

def parse_walks_allowed_per_nine_innings(cols):
    if len(cols) < 7:
        return None
    team_league = cols[1].get_text(strip=True)
    team, league = extract_team_league(team_league)

    win_loss_tie = cols[3].text.strip()
    parts = win_loss_tie.split('-')

    # Convert the parts to integers, filling in 0 if tie is missing
    wins = int(parts[0]) if len(parts) > 0 else 0
    losses = int(parts[1]) if len(parts) > 1 else 0
    tie = int(parts[2]) if len(parts) > 2 else 0

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'T': tie,
            'IP': float(cols[4].text.strip()),
            'BB (Pitching)': int(cols[5].text.strip()),
            'BBPG (Pitching)': float(cols[6].text.strip())
        }
    )

def extract_team_league(team_league_str):
    if '(' in team_league_str and ')' in team_league_str:
        team, league = team_league_str.rsplit('(', 1)
        return team.strip(), league.strip(')')
    return team_league_str.strip(), ''

def combine_team_stats(*stats_dicts):
    combined = {}

    for stat_dict in stats_dicts:
        for key, value in stat_dict.items():
            if stat_dict is None:
                continue
            # Convert tuple keys to a string (ex. "Team Name (League)")
            if isinstance(key, tuple):
                key_str = f"{key[0]} ({key[1]})"
            else:
                key_str = str(key)
            if key_str not in combined:
                combined[key_str] = {}
            filtered_value = {k: v for k, v in value.items() if k != 'rank'}
            combined[key_str].update(filtered_value)

    return combined

# Experimental Win Probability, not for use
def calculate_win_probability(team1_stats, team2_stats, combined_stats):
    stats = ['WPCT', 'ERA', 'OBP', 'BA']
    weights = {'WPCT': 1, 'ERA': 1, 'OBP': 1, 'BA': 1}

    # Multipliers for league strength (approximate; customize as needed)
    league_strengths = {
        # Tier 1: Power Conferences
        'SEC': 1.25,
        'ACC': 1.21,
        'Big 12': 1.18,
        'Pac-12': 1.15,
        'Big Ten': 1.12,

        # Tier 2: Upper-Mid Majors
        'The American': 1.08,
        'Sun Belt': 1.07,
        'CAA': 1.06,
        'Conference USA': 1.06,
        'Big West': 1.05,
        'ASUN': 1.04,
        'WCC': 1.04,

        # Tier 3: Mid-Majors / Upper-Low
        'Atlantic 10': 1.00,
        'MVC': 1.00,
        'Mountain West': 1.00,
        'MAC': 0.97,
        'Southland': 0.97,
        'SoCon': 0.96,
        'Patriot': 0.94,
        'DI Independent': 0.94,
        'Big South': 0.93,

        # Tier 4: Low-Majors
        'Horizon': 0.90,
        'America East': 0.90,
        'OVC': 0.89,
        'NEC': 0.88,
        'MAAC': 0.87,

        # Tier 5: Bottom Conferences
        'Ivy League': 0.83,
        'MEAC': 0.82,
        'SWAC': 0.82,
        'Summit League': 0.81,
        'WAC': 0.80
    }

    # Calculate means and stds
    stat_values = {stat: [stats_dict[stat] for stats_dict in
                          combined_stats.values() if stat in stats_dict] for stat in stats}
    stat_means = {stat: np.mean(vals) for stat, vals in stat_values.items()}
    stat_stds = {stat: max(np.std(vals), 1e-6) for stat, vals
                 in stat_values.items()}  # avoid zero division

    def score(team_stats):
        total = 0
        for stat in stats:
            if stat not in team_stats:
                continue
            z = (team_stats[stat] - stat_means[stat]) / stat_stds[stat]
            if stat == 'ERA':
                z *= -1  # lower is better
            total += z * weights[stat]
        league = team_stats.get('league', '')
        total *= league_strengths.get(league, 1.0)
        return total

    s1 = score(team1_stats)
    s2 = score(team2_stats)
    prob = 1 / (1 + np.exp(-(s1 - s2)))
    return round(prob, 4)

# Step 1: Final season stats based on year
RANKING_PERIODS = {
    2002: {1: 12.0, 2: 9.0, 3: 9.0},
    2003: {1: 12.0, 2: 8.0, 3: 8.0},
    2004: {1: 11.0, 2: 8.0, 3: 9.0},
    2005: {1: 13.0, 2: 11.0, 3: 12.0},
    2006: {1: 12.0, 2: 12.0, 3: 11.0},
    2007: {1: 13.0, 2: 12.0, 3: 11.0}, # Fully minimized amount of rankings ^^
    2008: {1: 17.0, 2: 13.0, 3: 12.0},
    2009: {1: 16.0, 2: 13.0, 3: 12.0},
    2010: {1: 16.0, 2: 12.0, 3: 12.0},
    2011: {1: 17.0, 2: 13.0, 3: 12.0},
    2012: {1: 35.0, 2: 16.0, 3: 15.0}, # Half minimized amount of rankings ^^
    2013: {1: 40.0, 2: 14.0, 3: 13.0},
    2014: {1: 43.0, 2: 14.0, 3: 13.0},
    2015: {1: 95.0, 2: 24.0, 3: 30.0},
    2016: {1: 100.0, 2: 32.0, 3: 36.0},
    2017: {1: 98.0, 2: 30.0, 3: 44.0},
    2018: {1: 95.0, 2: 47.0, 3: 71.0},
    2019: {1: 93.0, 2: 57.0, 3: 67.0},
    2020: {1: 23.0, 2: 23.0, 3: 26.0},
    2021: {1: 96.0, 2: 73.0, 3: 98.0},
    2022: {1: 90.0, 2: 78.0, 3: 103.0},
    2023: {1: 94.0, 2: 76.0, 3: 104.0},
    2024: {1: 108.0, 2: 79.0, 3: 105.0},
    2025: {1: 104.0, 2: 79.0, 3: 101.0}
}

# Step 2: URL builder
def build_ncaa_url(stat_seq, year=2025, division=1):
    try:
        ranking_period = RANKING_PERIODS[year][division]
    except KeyError:
        raise ValueError(f"Ranking period not defined for year {year} and division {division}")

    return (
        f"https://stats.ncaa.org/rankings/national_ranking?"
        f"academic_year={float(year)}&division={float(division)}&"
        f"ranking_period={ranking_period}&sport_code=MBA&stat_seq={float(stat_seq)}"
    )


# Step 3: Factory function to generate stat fetchers
def make_stat_func(stat_seq, parser, valid_years=None):
    def stat_func(year=2025, division=1):
        if valid_years is not None and year not in valid_years:
            print(f"Skipping year {year} for stat_seq {stat_seq} – not a valid year.")
            return None
        url = build_ncaa_url(stat_seq=stat_seq, year=year, division=division)
        return fetch_ncaa_table(url, parser)
    return stat_func


# Step 4: Refactored functions using the factory
base_on_balls = make_stat_func(496.0, parse_base_on_balls_row,
                                 valid_years=list(range(2008, 2026)))
batting_average = make_stat_func(210.0, parse_batting_average,
                                 valid_years=list(range(2002, 2026)))
double_plays_per_game = make_stat_func(328.0, parse_double_plays_per_game,
                                 valid_years=list(range(2003, 2026)))
double_plays = make_stat_func(501.0, parse_double_plays,
                                 valid_years=list(range(2008, 2026)))
doubles = make_stat_func(489.0, parse_doubles,
                                 valid_years=list(range(2008, 2026)))
doubles_per_game = make_stat_func(324.0, parse_doubles_per_game,
                                 valid_years=list(range(2002, 2026)))
earned_run_average = make_stat_func(211.0, parse_earned_run_average,
                                 valid_years=list(range(2002, 2026)))
fielding_percentage = make_stat_func(212.0, parse_fielding_percentage,
                                 valid_years=list(range(2002, 2026)))
hit_batters = make_stat_func(593.0, parse_hit_batters, valid_years=list(range(2013, 2026)))
hit_by_pitch = make_stat_func(500.0, parse_hit_by_pitch,
                                 valid_years=list(range(2008, 2026)))
hits = make_stat_func(484.0, parse_hits,
                                 valid_years=list(range(2008, 2026)))
hits_allowed_per_nine_innings = make_stat_func(506.0, parse_hits_allowed_per_nine_innings,
                                 valid_years=list(range(2008, 2026)))
home_runs = make_stat_func(513.0, parse_home_runs,
                                 valid_years=list(range(2008, 2026)))
home_runs_per_game = make_stat_func(323.0, parse_home_runs_per_game,
                                 valid_years=list(range(2002, 2026)))
on_base_percentage = make_stat_func(589.0, parse_on_base_percentage,
                                 valid_years=list(range(2012, 2026)))
runs = make_stat_func(486.0, parse_runs, valid_years=list(range(2008, 2026)))
sacrifice_bunts = make_stat_func(498.0, parse_sacrifice_bunts,
                                 valid_years=list(range(2008, 2026)))
sacrifice_flies = make_stat_func(503.0, parse_sacrifice_flies,
                                 valid_years=list(range(2008, 2026)))
scoring = make_stat_func(213.0, parse_scoring, valid_years=list(range(2002, 2026)))
shutouts = make_stat_func(691.0, parse_shutouts, valid_years=list(range(2013, 2026)))
slugging_percentage = make_stat_func(327.0, parse_slugging_percentage,
                                 valid_years=list(range(2003, 2026)))
stolen_bases = make_stat_func(493.0, parse_stolen_bases,
                              valid_years=list(range(2002, 2026)))
stolen_bases_per_game = make_stat_func(326.0, parse_stolen_bases_per_game,
                                 valid_years=list(range(2008, 2026)))
strikeout_to_walk_ratio = make_stat_func(591.0, parse_strikeout_to_walk_ratio,
                                 valid_years=list(range(2012, 2026)))
strikeouts_per_nine_innings = make_stat_func(425.0, parse_strikeouts_per_nine_innings,
                                 valid_years=list(range(2008, 2026)))
triple_plays = make_stat_func(598.0, parse_triple_plays,
                              valid_years=list(range(2013, 2026)))
triples = make_stat_func(491.0, parse_triples,
                                 valid_years=list(range(2008, 2026)))
triples_per_game = make_stat_func(325.0, parse_triples_per_game,
                                 valid_years=list(range(2002, 2026)))
whip = make_stat_func(597.0, parse_whip, valid_years=list(range(2012, 2026)))
winning_percentage = make_stat_func(319.0, parse_winning_percentage,
                                 valid_years=list(range(2011, 2026)))
walks_allowed_per_nine_innings = make_stat_func(509.0, parse_walks_allowed_per_nine_innings,
                                 valid_years=list(range(2011, 2026)))