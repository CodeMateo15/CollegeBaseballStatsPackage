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
            print(f"\nStats for {team}:")
            for stat_name, value in stats.items():
                print(f"  {stat_name}: {value}")

    if not found:
        print("No team found matching the search term.")


def get_pythagenpat_expectation(team_name: str, year: int, division: int) -> str:
    """
    Computes Pythagenpat expected win percentage and compares it with the actual win percentage.

    Args:
        team_name: Team name or partial string (ex. "Northeastern").
        year: NCAA season year.
        division: NCAA division (1, 2, or 3).

    Returns:
        A string summary with expected and actual win percentages.
    """
    exponent = 1.83
    R = get_team_stat("R (Batting)", team_name, year, division)
    RA = get_team_stat("R (Pitching)", team_name, year, division)
    W = get_team_stat("W", team_name, year, division)
    L = get_team_stat("L", team_name, year, division)
    T = get_team_stat("T", team_name, year, division)

    if None in (R, RA, W, L, T):
        return f"Insufficient data to compute Pythagenpat for '{team_name}' ({year}, Div {division})."

    try:
        expected_pct = R**exponent / (R**exponent + RA**exponent)
        total_games = W + L + T
        actual_pct = W / total_games if total_games > 0 else 0.0

        return (
            f"Pythagenpat Expected Win% for {team_name} ({year}, Div {division}): {expected_pct:.3f} | "
            f"Actual Win%: {actual_pct:.3f}"
        )
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        return f"Could not compute Pythagenpat for '{team_name}': {str(e)}"


MLB_DRAFT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "mlb_draft_cache"))

def load_draft_data(year=None):
    """
    Loads MLB draft picks for a specific year or all years.

    Args:
        year (int or None): The year to load, or None for all years.
    Returns:
        List of draft pick dicts.
    """
    if year:
        path = os.path.join(MLB_DRAFT_DIR, f"{year}.json")
    else:
        path = os.path.join(MLB_DRAFT_DIR, "all_drafts.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Draft data file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def get_drafted_players_mlb(team_name: str, year: int) -> list:
    """
    Returns a list of player names drafted by a MLB team for a given year.
    Args:
        team_name (str): ex. "Baltimore Orioles"
        year (int): ex. 2019
    Returns:
        List of dicts for each draft pick.
    """
    picks = load_draft_data(year)
    return [p for p in picks if team_name.lower() in p.get("Drafted By", "").lower()]


def get_drafted_players_all_years_mlb(team_name: str) -> list:
    """
    Returns all players drafted by a MLB team across all years.
    """
    picks = load_draft_data()  # all_drafts.json
    return [p for p in picks if team_name.lower() in p.get("Drafted By", "").lower()]

def get_drafted_players_college(team_name: str, year: int) -> list:
    """
    Returns a list of player names drafted from a college team for a given year.
    Args:
        team_name (str): e.g. "Baltimore Orioles"
        year (int): e.g. 2019
    Returns:
        List of dicts for each draft pick.
    """
    picks = load_draft_data(year)
    return [p for p in picks if team_name.lower() in p.get("Drafted From", "").lower()]


def get_drafted_players_all_years_college(team_name: str) -> list:
    """
    Returns all players drafted from a college team across all years.
    """
    picks = load_draft_data()  # all_drafts.json
    return [p for p in picks if team_name.lower() in p.get("Drafted From", "").lower()]


def print_draft_picks_mlb(picks: list):
    """
    Prints formatted draft pick info from a list of draft dicts for MLB teams.
    """
    for p in picks:
        print(f"{p['Year']} Round {p['Round']} Pick {p['Pick']}: {p['Player Name']} - {p['POS']} from {p['Drafted From']}")


def print_draft_picks_college(picks: list):
    """
    Prints formatted draft pick info from a list of draft dicts for college teams.
    """
    for p in picks:
        print(f"{p['Year']} Round {p['Round']} Pick {p['Pick']}: {p['Player Name']} - {p['POS']} for {p['Drafted By']}")
