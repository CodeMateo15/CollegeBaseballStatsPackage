import json
import os
from src.stats import *
'''
bb = base_on_balls()
ba = batting_average()
dp = double_plays()
dppg = double_plays_per_game()
d = doubles()
dpg = doubles_per_game()
era = earned_run_average()
fpct = fielding_percentage()
hb = hit_batters()
hbp = hit_by_pitch()
h = hits()
hapni = hits_allowed_per_nine_innings()
hr = home_runs()
hrpg = home_runs_per_game()
obp = on_base_percentage()
r = runs()
sb = sacrifice_bunts()
sf = sacrifice_flies()
s = scoring()
so = shutouts()
spct = slugging_percentage()
sb = stolen_bases()
sbpg = stolen_bases_per_game()
sowr = strikeout_to_walk_ratio()
sopni = strikeouts_per_nine_innings()
tp = triple_plays()
t = triples()
tpg = triples_per_game()
whip = whip()
wpct = winning_percentage()
wapni = walks_allowed_per_nine_innings()

for team in whip.values():
    print(f"{team['rank']}. {team['team']} ({team['league']}) - {team['IP']} - {team['WHIP']}")

combined_stats = combine_team_stats(wpct, bb, ba, dp, dppg, d, dpg, era, fpct, hb, hbp, h, hapni, hr, hrpg, obp, r, sb, sf, s, so, spct, sb, sbpg, sowr, sopni, tp, t, tpg, whip, wapni)

#for key, stats in list(combined_stats.items())[:5]: 
#    print(f"{key}: {stats}")

# Search for a specific team
search_team = "Northeastern"
found = False
for (team, league), stats in combined_stats.items():
    if search_team.lower() in team.lower():
        print(f"\nStats for {team} ({league}):")
        for stat_name, value in stats.items():
            print(f"  {stat_name}: {value}")
        found = True

if not found:
    print(f"No data found for team: {search_team}")


team1_name = "Northeastern"
team2_name = "Mississippi St."
team3_name = "Florida St."
team4_name = "North Carolina"

team1_stats = None
team2_stats = None
team3_stats = None
team4_stats = None

for (team, league), stats in combined_stats.items():
    if team1_name.lower() in team.lower():
        team1_stats = stats
    elif team2_name.lower() in team.lower():
        team2_stats = stats
    elif team3_name.lower() in team.lower():
        team3_stats = stats
    elif team4_name.lower() in team.lower():
        team4_stats = stats

if team1_stats and team2_stats:
    prob = calculate_win_probability(team1_stats, team2_stats, combined_stats)
    print(f"\nWin Probability: {team1_name} vs {team2_name}")
    print(f"{team1_name} chance of winning: {prob*100:.2f}%")
    print(f"{team2_name} chance of winning: {(1-prob)*100:.2f}%")
else:
    print("Could not find both teams in the data.")

if team1_stats and team3_stats:
    prob = calculate_win_probability(team1_stats, team3_stats, combined_stats)
    print(f"\nWin Probability: {team1_name} vs {team3_name}")
    print(f"{team1_name} chance of winning: {prob*100:.2f}%")
    print(f"{team3_name} chance of winning: {(1-prob)*100:.2f}%")
else:
    print("Could not find both teams in the data.")

if team1_stats and team4_stats:
    prob = calculate_win_probability(team1_stats, team4_stats, combined_stats)
    print(f"\nWin Probability: {team1_name} vs {team4_name}")
    print(f"{team1_name} chance of winning: {prob*100:.2f}%")
    print(f"{team4_name} chance of winning: {(1-prob)*100:.2f}%")
else:
    print("Could not find both teams in the data.")
'''

def get_team_stat(stat_name: str, team_name: str, year: int, division: int) -> float | int | None:
    """
    Returns a specific stat for a team in a given year and division.

    This function searches through cached or pre-scraped data to find
    the matching team and returns its statistics.

    Args:
        stat_name: The name of the stat (ex. "home_runs").
        team_name: The team name (ex. "Northeastern").
        year: The year (ex. 2015).
        division: The NCAA division (1, 2, or 3).

    Returns:
        The stat value (int/float), or None if not found.
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data", "team_stats", f"div{division}", f"{year}.json"
    )

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Stats for Division {division} in {year} not found.")

    with open(file_path, "r") as f:
        stats = json.load(f)

    # Case-insensitive search
    for team, team_stats in stats.items():
        if team_name.lower() in team.lower():
            return team_stats.get(stat_name)

    return None


def display_specific_team_stat(stat_name: str, search_team: str, year: int, division: int) -> None:
    """
    Displays a specific stat for all teams matching a name substring in a given division and year.

    Args:
        stat_name: The name of the stat to display (e.g., "home_runs").
        search_team: Substring to match against team names (e.g., "Northeastern").
        year: The year of the stats file (e.g., 2015).
        division: NCAA division number (1, 2, or 3).

    Returns:
        None. Prints the stat for each matching team.
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data", "team_stats", f"div{division}", f"{year}.json"
    )

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Stats for Division {division} in {year} not found.")

    with open(file_path, "r") as f:
        all_teams = json.load(f)

    found = False
    for team, stats in all_teams.items():
        if search_team.lower() in team.lower():
            found = True
            league = stats.get("league", "Unknown League")
            value = stats.get(stat_name)
            if value is not None:
                print(f"{team} ({league}) - {stat_name}: {value}")
            else:
                print(f"{team} ({league}) - Stat '{stat_name}' not found.")

    if not found:
        print("No team found matching the search term.")


def display_team_stats(search_team: str, year: int, division: int) -> None:
    """
    Displays all statistics for teams matching a name substring in a specific NCAA division and year.

    Args:
        search_team: Substring to match against team names (ex. "Northeastern").
        year: The year of the stats file (ex. 2015).
        division: NCAA division number (1, 2, or 3).

    Returns:
        None. Prints matching teams and their stats to the console.
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data", "team_stats", f"div{division}", f"{year}.json"
    )

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Stats for Division {division} in {year} not found.")

    with open(file_path, "r") as f:
        all_teams = json.load(f)

    found = False
    for team, stats in all_teams.items():
        if search_team.lower() in team.lower():
            found = True
            league = stats.get("league", "Unknown League")
            print(f"\nStats for {team} ({league}):")
            for stat_name, value in stats.items():
                print(f"  {stat_name}: {value}")

    if not found:
        print("No team found matching the search term.")


def main():
    # Example user input
    year = 2017
    division = 3

    try:
        # Call a stat function with the year/division
        data = hit_batters(year=year, division=division)
        print("Hit Batters data:")
        print(data)

        # Call another stat for same or different config
        ba_data = batting_average(year=year, division=division)
        print("\nBatting Average data:")
        print(ba_data)

    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()


