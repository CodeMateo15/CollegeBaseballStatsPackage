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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'BB (Batting)': int(cols[4].text.strip())
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'DP': int(cols[4].text.strip()),
            'DPPG': float(cols[5].text.strip())
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'DP': int(cols[4].text.strip())
        }
    )

def parse_doubles(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            '2B': int(cols[4].text.strip())
        }
    )

def parse_doubles_per_game(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            '2B': int(cols[4].text.strip()),
            '2BPG': float(cols[5].text.strip())
        }
    )

def parse_earned_run_average(cols):
    if len(cols) < 8:
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'IP': float(cols[4].text.strip()),
            'HB': int(cols[5].text.strip())
        }
    )

def parse_hit_by_pitch(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'HBP': float(cols[4].text.strip())
        }
    )

def parse_hits(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'AB': int(cols[4].text.strip().replace(',', '')),
            'H': int(cols[5].text.strip())
        }
    )

def parse_hits_allowed_per_nine_innings(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'HR': int(cols[4].text.strip())
        }
    )

def parse_home_runs_per_game(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'HR': int(cols[4].text.strip()),
            'HRPG': float(cols[5].text.strip())
        }
    )

def parse_on_base_percentage(cols):
    if len(cols) < 11:
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'R (Batting)': int(cols[4].text.strip())
        }
    )

def parse_sacrifice_bunts(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'SH': int(cols[4].text.strip())
        }
    )

def parse_sacrifice_flies(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'SF': int(cols[4].text.strip())
        }
    )

def parse_scoring(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'R (Batting)': int(cols[4].text.strip()),
            'RPG': float(cols[5].text.strip())
        }
    )

def parse_shutouts(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'SHO': int(cols[4].text.strip())
        }
    )

def parse_slugging_percentage(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'SB': int(cols[4].text.strip()),
            'CS': int(cols[5].text.strip())
        }
    )

def parse_stolen_bases_per_game(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'SB': int(cols[4].text.strip()),
            'CS': int(cols[5].text.strip()),
            'SBPG': int(cols[6].text.strip())
        }
    )

def parse_strikeout_to_walk_ratio(cols):
    if len(cols) < 8:
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            'TP': int(cols[4].text.strip())
        }
    )

def parse_triples(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            '3B': int(cols[4].text.strip())
        }
    )

def parse_triples_per_game(cols):
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
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
            '3B': int(cols[4].text.strip()),
            '3BPG': float(cols[5].text.strip())
        }
    )

def parse_whip(cols):
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
            'W': wins,
            'L': losses,
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

    win_loss = cols[3].text.strip()
    wins, losses = map(int, win_loss.split('-'))

    return (
        (team, league),
        {
            'rank': cols[0].text.strip(),
            'team': team,
            'league': league,
            'G': int(cols[2].text.strip()),
            'W': wins,
            'L': losses,
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


def calculate_win_probability(team1_stats, team2_stats, weights=None):
    if not weights:
        # Default equal weights for normalized stats
        weights = {
            'WPCT': 1.5, 'ERA': -1.0, 'WHIP': -1.0, 'OBP': 1.2,
            'SLG': 1.2, 'R (Batting)': 1.0, 'HR': 0.8, 'SB': 0.5,
            'K/BB': 0.8, 'FPCT': 0.5, 'RPG': 1.0
        }

    def score(stats):
        total = 0
        for stat, weight in weights.items():
            val = stats.get(stat)
            if val is not None:
                total += val * weight
        return total

    team1_score = score(team1_stats)
    team2_score = score(team2_stats)

    if team1_score + team2_score == 0:
        return 0.5  # Avoid division by zero

    prob_team1_wins = team1_score / (team1_score + team2_score)
    return round(prob_team1_wins, 4)


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