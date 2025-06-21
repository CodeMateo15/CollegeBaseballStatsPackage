from stats import *
# from saveSQL import create_stats_database, get_win_probability
from player_stats import *
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
if __name__ == "__main__":
    # Example usage:
    # create_stats_database()
    # print(get_win_probability("Northeastern", "Mississippi St."))

    for year in range(2024, 2025):
        url = f'https://d1baseball.com/statistics/?season={year}'
        print(f"📅 Processing season {year}...")

        batters = fetch_player_stats(stat_type='batting', url=url)


        pitchers = fetch_player_stats(stat_type='pitching', url=url)

    # Example: print top 5 batting stats
    for player in batters:
        print(player)

    print("------------")

    for player in pitchers[:1]:
        print(player)

