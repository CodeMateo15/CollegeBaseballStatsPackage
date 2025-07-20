import os
import json

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
        "..", "data", "team_stats_cache", f"div{division}", f"{year}.json"
    )
    file_path = os.path.abspath(file_path)

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
        "..", "data", "team_stats_cache", f"div{division}", f"{year}.json"
    )
    file_path = os.path.abspath(file_path)

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
                print(f"{team} - {stat_name}: {value}")
            else:
                print(f"{team} - Stat '{stat_name}' not found.")

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
        "..", "data", "team_stats_cache", f"div{division}", f"{year}.json"
    )
    file_path = os.path.abspath(file_path)

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Stats for Division {division} in {year} not found.")

    with open(file_path, "r") as f:
        all_teams = json.load(f)

    found = False
    for team, stats in all_teams.items():
        if search_team.lower() in team.lower():
            found = True
            league = stats.get("league", "Unknown League")
            print(f"\nStats for {team}:")
            for stat_name, value in stats.items():
                print(f"  {stat_name}: {value}")

    if not found:
        print("No team found matching the search term.")