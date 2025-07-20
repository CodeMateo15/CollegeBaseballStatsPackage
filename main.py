from src.ncaa_bbStats.stats import *

'''

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


