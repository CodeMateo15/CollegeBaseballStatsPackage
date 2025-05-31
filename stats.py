import requests
from bs4 import BeautifulSoup
import time
import numpy as np

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
            if key not in combined:
                combined[key] = {}

            # Exclude the 'rank' key from each stat entry
            filtered_value = {k: v for k, v in value.items() if k != 'rank'}
            combined[key].update(filtered_value)

    return combined


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
    stat_values = {stat: [stats_dict[stat] for stats_dict in combined_stats.values() if stat in stats_dict] for stat in stats}
    stat_means = {stat: np.mean(vals) for stat, vals in stat_values.items()}
    stat_stds = {stat: max(np.std(vals), 1e-6) for stat, vals in stat_values.items()}  # avoid zero division

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


# Edit these to include input on academic year and division
def base_on_balls():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=496.0"
    return fetch_ncaa_table(url, parse_base_on_balls_row)

def batting_average():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=210.0"
    return fetch_ncaa_table(url, parse_batting_average)

def double_plays_per_game():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=328.0"
    return fetch_ncaa_table(url, parse_double_plays_per_game)

def double_plays():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=501.0"
    return fetch_ncaa_table(url, parse_double_plays)

def doubles():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=489.0"
    return fetch_ncaa_table(url, parse_doubles)

def doubles_per_game():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=324.0"
    return fetch_ncaa_table(url, parse_doubles_per_game)

def earned_run_average():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=211.0"
    return fetch_ncaa_table(url, parse_earned_run_average)

def fielding_percentage():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=212.0"
    return fetch_ncaa_table(url, parse_fielding_percentage)

def hit_batters():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=593.0"
    return fetch_ncaa_table(url, parse_hit_batters)

def hit_by_pitch():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=500.0"
    return fetch_ncaa_table(url, parse_hit_by_pitch)

def hits():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=484.0"
    return fetch_ncaa_table(url, parse_hits)

def hits_allowed_per_nine_innings():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=506.0"
    return fetch_ncaa_table(url, parse_hits_allowed_per_nine_innings)

def home_runs():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=513.0"
    return fetch_ncaa_table(url, parse_home_runs)

def home_runs_per_game():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=323.0"
    return fetch_ncaa_table(url, parse_home_runs_per_game)

def on_base_percentage():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=589.0"
    return fetch_ncaa_table(url, parse_on_base_percentage)

def runs():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=486.0"
    return fetch_ncaa_table(url, parse_runs)

def sacrifice_bunts():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=498.0"
    return fetch_ncaa_table(url, parse_sacrifice_bunts)

def sacrifice_flies():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=503.0"
    return fetch_ncaa_table(url, parse_sacrifice_flies)

def scoring():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=213.0"
    return fetch_ncaa_table(url, parse_scoring)

def shutouts():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=691.0"
    return fetch_ncaa_table(url, parse_shutouts)

def slugging_percentage():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=327.0"
    return fetch_ncaa_table(url, parse_slugging_percentage)

def stolen_bases():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=493.0"
    return fetch_ncaa_table(url, parse_stolen_bases)

def stolen_bases_per_game():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=326.0"
    return fetch_ncaa_table(url, parse_stolen_bases_per_game)

def strikeout_to_walk_ratio():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=591.0"
    return fetch_ncaa_table(url, parse_strikeout_to_walk_ratio)

def strikeouts_per_nine_innings():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=425.0"
    return fetch_ncaa_table(url, parse_strikeouts_per_nine_innings)

def triple_plays():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=598.0"
    return fetch_ncaa_table(url, parse_triple_plays)

def triples():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=491.0"
    return fetch_ncaa_table(url, parse_triples)

def triples_per_game():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=325.0"
    return fetch_ncaa_table(url, parse_triples_per_game)

def whip():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=597.0"
    return fetch_ncaa_table(url, parse_whip)

def winning_percentage():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=319.0"
    return fetch_ncaa_table(url, parse_winning_percentage)

def walks_allowed_per_nine_innings():
    url = "https://stats.ncaa.org/rankings/national_ranking?academic_year=2025.0&division=1.0&ranking_period=86.0&sport_code=MBA&stat_seq=509.0"
    return fetch_ncaa_table(url, parse_walks_allowed_per_nine_innings)