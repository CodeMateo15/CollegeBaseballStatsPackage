# ncaa_bbStats (AKA CollegeBaseballStatsPackage)

**ncaa_bbStats** is an open-source Python package for retrieving, parsing, and analyzing Division I, II, and III college baseball team statistics (2002–2025). It also includes tools to retrieve and analyze MLB draft results of NCAA players. Built for sports analysts, developers, and fans, the package supports both live scraping and cached JSON access for faster use.

> **Note**  
> This project is under active development.

---

## Documentation  
Documentation is available at: <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/index.html" target="_blank">ncaa_bbStats's ReadTheDocs</a>

PyPI site: <a href="https://pypi.org/project/ncaa-bbStats/" target="_blank">Link</a>

---

## Install
```bash
pip install ncaa_bbStats
```
## Team Stats Module
### Overview
This module enables you to extract season statistics for college baseball teams across all NCAA divisions. Some examples you can retrieve include:

Batting Stats: BA, HR, 2B, 3B, OBP, SLG

Pitching Stats: ERA, WHIP, K/9, SHO

Fielding Stats: FPCT, E, DP, TP

### Retrieval Functions
```
get_team_stat(stat_name: str, team_name: str, year: int, division: int): Retrieves a specific statistic for a given team from the cached data
```
```
display_specific_team_stat(stat_name: str, search_team: str, year: int, division: int): Prints a specific statistic for a team in a readable format
```
```
display_team_stats(search_team: str, year: int, division: int): Displays all available statistics for a team for a given year and division
```
```
list_all_teams(year: int, division: int): Lists all teams for a given year and division
```
### Statistical Analysis Functions
```
average_all_team_stats(year: int, division: int): Computes the average of all numeric values for each statistic across all teams
```
```
average_team_stat_str(stat_name: str, year: int, division: int): Returns a string representing the average value of a given statistic across all teams for the specified year and division
```
```
average_team_stat_float(stat_name: str, year: int, division: int): Returns a float representing the average value of a given statistic across all teams for the specified year and division
```
```
get_pythagorean_expectation(team_name: str, year: int, division: int): Computes Pythagorean expected win percentage
```
```
compare_pythagorean_expectation(team_name: str, year: int, division: int): Computes Pythagorean expected win percentage and compares it with the actual win percentage
```
```
plot_team_stat_over_years(stat_name: str, team_name: str, division: int, start_year: int, end_year: int): Aggregates and plots a specified statistic for a team over a range of years
```
### JSON Caching
Stats are stored in local JSON files (/data/team_stats_cache/) to enable fast offline access.

## Draft Module
### Overview
This module pulls MLB draft data for college baseball players and formats it for analysis.

### Functions
```
parse_mlb_draft(year: int): Parses MLB draft results from Baseball Almanac for a given year (1965–2025)
```
```
get_drafted_players_mlb(team_name: str, year: int): Retrieves a list of players from the specified team drafted to MLB in a given year
```
```
get_drafted_players_all_years_mlb(team_name: str): Retrieves all MLB draft picks for a team across all available years
```
```
get_drafted_players_college(team_name: str, year: int): Retrieves a list of players from the specified team drafted to college in a given year
```
```
get_drafted_players_all_years_college(team_name: str): Retrieves all college draft picks for a team across all available years
```
```
print_draft_picks_mlb(picks: list): Prints MLB draft picks for a team in a given year in a readable format
```
```
print_draft_picks_college(picks: list): Prints college draft picks for a team in a given year in a readable format
```

## Player Stats Module
### Overview
Simple, notebook-friendly helpers to explore player batting and pitching stats from cached CSVs (qualified and noMin).

- Discover available years and players
- Retrieve specific stats as floats or lists
- Get player rows for a season or across seasons
- Build quick leaderboards (top-N)

### Functions
```
list_available_years(stat_type: "batting"|"pitching", qualifier: "qualified"|"noMin"): Sorted unique years available for the given stat type and qualifier
```
```
list_players(stat_type: "batting"|"pitching", qualifier: "qualified"|"noMin", year: int|None = None, team_substr: str|None = None): List player names, optionally filtered by a specific year and team substring
```
```
player_seasons(stat_type: "batting"|"pitching", qualifier: "qualified"|"noMin", player_name: str): Years in which the player appears in the chosen dataset
```
```
get_player_rows(stat_type: "batting"|"pitching", qualifier: "qualified"|"noMin", player_name: str, year: int|None = None, team_substr: str|None = None, include_columns: list[str]|None = None): Return per-row dictionaries for a player, optionally filtered by year and team substring
```
```
top_players(stat_type: "batting"|"pitching", stat: str, n: int = 10, year: int|None = None, team_substr: str|None = None): Top-N leaderboard for a given stat. Uses the "qualified" dataset internally
```
```
batting_stat(player_name: str, stat: str, qualifier: "qualified"|"noMin" = "noMin", year: int|None = None, team_substr: str|None = None): Get a batting stat for a player from the selected dataset, optionally filtered by year and team
```
```
pitching_stat(player_name: str, stat: str, qualifier: "qualified"|"noMin" = "noMin", year: int|None = None, team_substr: str|None = None): Get a pitching stat for a player from the selected dataset, optionally filtered by year and team
```
```
list_batters(qualifier: "qualified"|"noMin" = "noMin", year: int|None = None, team_substr: str|None = None): List batter names from the selected dataset, optionally filtered by year and team substring
```
```
list_pitchers(qualifier: "qualified"|"noMin" = "noMin", year: int|None = None, team_substr: str|None = None): List pitcher names from the selected dataset, optionally filtered by year and team substring
```

### Quick Examples
```python
from ncaa_bbStats import (
    list_available_years,
    list_batters,
    batting_stat,
    top_players,
    get_player_rows,
)

years = list_available_years("batting", "qualified")
latest = years[-1]

# List batter names (noMin) for the latest year
batters = list_batters("noMin", year=latest)

# Top 5 HR leaders (qualified)
leaders = top_players("batting", "hr", n=5, year=latest)

# Player HR total (noMin)
if batters:
    hr_total = batting_stat(batters[0], "hr", qualifier="noMin", year=latest)

# Selected columns for a player in a season
rows = get_player_rows("batting", "noMin", batters[0], year=latest, include_columns=["name","team","year","hr","pa"])
```

## Reference
### Season Stats Reference
See full list of supported team statistics and their abbreviations in the <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/season_stats.html" target="_blank">Stats List</a>.

### Team Names
Refer to <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/team_names_stats.html" target="_blank">Team Name Reference</a> for formatting options when passing team names.

### Draft Team/School Names
Use the <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/team_names_mlb.html" target="_blank">MLB Draft Name Reference</a> for consistent naming of schools when using draft-related functions.

## Planned Features

- Team game results with win-loss tracking

- Win probability models using in-game data

## Support
Star this repo and share to help support!
[![GitHub stars](https://img.shields.io/github/stars/CodeMateo15/CollegeBaseballStatsPackage.svg?style=social&label=Star)](https://github.com/CodeMateo15/CollegeBaseballStatsPackage)

## Contact
Feel free to reach out for collaboration or feedback:
Mateo Biggs, mateojohn2024@gmail.com
