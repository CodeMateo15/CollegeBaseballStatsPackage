from stats import base_on_balls, batting_average, double_plays_per_game, double_plays, combine_team_stats

dp = double_plays()
dppg = double_plays_per_game()
bb = base_on_balls()
ba = batting_average()

#for team in dp.values():
#    print(f"{team['rank']}. {team['team']} ({team['league']}) - {team['games']} - {team['wins']} - {team['double_play']}")

combined_stats = combine_team_stats(bb, dp, dppg, ba)

#for key, stats in list(combined_stats.items())[:5]:
#    print(f"{key}: {stats}")

# Search for a specific team
search_team = "South Fla."
found = False
for (team, league), stats in combined_stats.items():
    if search_team.lower() in team.lower():
        print(f"\nStats for {team} ({league}):")
        for stat_name, value in stats.items():
            print(f"  {stat_name}: {value}")
        found = True

if not found:
    print(f"No data found for team: {search_team}")