import os
import json

def average_all_team_stats(year: int, division: int) -> dict:
    """
     This function loads team statistics from a cached JSON file located in the
     `data/team_stats_cache/div{division}/{year}.json` path, then computes the
     average of all numeric values for each statistic across all teams.

     Args:
         year (int): The year of the statistics.
         division (int): The NCAA division (ex. 1, 2, or 3).

     Returns:
         dict: A dictionary mapping each statistic name to its average value.
     """
    file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "data", "team_stats_cache",
            f"div{division}", f"{year}.json"
        )
    )

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Stats for Division {division} in {year} not found.")

    with open(file_path, "r") as f:
        teams = json.load(f)

    stat_sums = {}
    stat_counts = {}

    for stats in teams.values():
        if not isinstance(stats, dict):
            continue  # Skip malformed entries

        for key, val in stats.items():
            if isinstance(val, (int, float)):
                stat_sums[key] = stat_sums.get(key, 0) + val
                stat_counts[key] = stat_counts.get(key, 0) + 1

    return {
        k: round(stat_sums[k] / stat_counts[k], 3)
        for k in stat_sums if stat_counts[k] > 0
    }


def average_team_stat_str(stat_name: str, year: int, division: int) -> str:
    """
    Returns a string representing the average value of a given statistic
    across all teams for the specified year and division.

    Args:
        stat_name (str): The name of the statistic to average.
        year (int): The year of the statistics.
        division (int): The NCAA division (ex. 1, 2, or 3).

    Returns:
        str: A string with the average value, or an error message if
             the statistic is not found.
    """
    avg_stat = average_team_stat_float(stat_name, year, division)
    if avg_stat is None:
        return f"Stat '{stat_name}' not found for Division {division} in {year}."
    return f"Avg {stat_name} for Division {division} in {year}: {avg_stat:.3f}"


def average_team_stat_float(stat_name: str, year: int, division: int) -> float | None:
    """
    This function loads statistics from a cached JSON file and computes the mean
    of the specified statistic, if available.

    Args:
        stat_name (str): The name of the statistic to average.
        year (int): The year of the statistics.
        division (int): The NCAA division (ex. 1, 2, or 3).

    Returns:
        float | None: The average value of the statistic rounded to three decimal
                      places, or None if the statistic is not found for any team.
    """
    file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "data", "team_stats_cache",
            f"div{division}", f"{year}.json"
        )
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Stats for Division {division} in {year} not found.")

    with open(file_path, "r") as f:
        teams = json.load(f)

    values = [
        stats.get(stat_name)
        for stats in teams.values()
        if isinstance(stats, dict) and isinstance(stats.get(stat_name), (int, float))
    ]

    if not values:
        return None

    return round(sum(values) / len(values), 3)
