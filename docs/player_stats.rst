Player Stats Module
===================

The `player_utils` module provides simple, notebook-friendly helpers for accessing college baseball player statistics (batting and pitching) from cached CSV files. Functions return basic Python types (lists, floats, dicts) to make exploration and analysis quick and ergonomic.

Overview
--------

This module lets you:

- Discover available years and players for batting or pitching datasets (qualified and noMin).
- Retrieve specific stats for a player as a float or list of values.
- Get player row records for a season or across seasons.
- Produce simple leaderboards (top-N) for common stats like HR, RBI, ERA, SO, etc.

Functions
---------

.. py:function:: list_available_years(stat_type: ["batting", "pitching"], qualifier: ["qualified", "noMin"]) -> list[int]

    Sorted unique years available for the given stat type and qualifier.

    :param stat_type: "batting" or "pitching".
    :param qualifier: "qualified" or "noMin" dataset.
    :return: Sorted list of years.

.. py:function:: list_players(stat_type: ["batting", "pitching"], qualifier: ["qualified", "noMin"], year: int | None = None, team_substr: str | None = None) -> list[str]

    List player names, optionally filtered by a specific year and team substring.

    :param stat_type: "batting" or "pitching".
    :param qualifier: "qualified" or "noMin" dataset.
    :param year: Optional year to filter by.
    :param team_substr: Optional case-insensitive team substring match.
    :return: Sorted list of player names.

.. py:function:: player_seasons(stat_type: ["batting", "pitching"], qualifier: ["qualified", "noMin"], player_name: str) -> list[int]

    Years in which the player appears in the chosen dataset.

    :param stat_type: "batting" or "pitching".
    :param qualifier: "qualified" or "noMin" dataset.
    :param player_name: Player's full name.
    :return: Sorted list of years.

.. py:function:: get_player_rows(stat_type: ["batting", "pitching"], qualifier: ["qualified", "noMin"], player_name: str, year: int | None = None, team_substr: str | None = None, include_columns: Sequence[str] | None = None) -> list[dict]

    Return per-row dictionaries for a player, optionally filtered by year and team substring.

    :param stat_type: "batting" or "pitching".
    :param qualifier: "qualified" or "noMin" dataset.
    :param player_name: Player's full name (case-insensitive match).
    :param year: Optional single year.
    :param team_substr: Optional case-insensitive team substring match.
    :param include_columns: Optional subset of columns to keep if present.
    :return: List of row dicts.

.. py:function:: top_players(stat_type: ["batting", "pitching"], stat: str, n: int = 10, year: int | None = None, team_substr: str | None = None) -> list[dict]

    Top-N leaderboard for a given stat. Uses the "qualified" dataset internally.

    :param stat_type: "batting" or "pitching".
    :param stat: Column name (case-insensitive), ex. "hr", "rbi", "obp", "era", "so".
    :param n: Number of rows to return (default 10).
    :param year: Optional year filter.
    :param team_substr: Optional case-insensitive team substring match.
    :return: List of dicts with keys: {"name", "team", "year", "value"}.

.. py:function:: batting_stat(player_name: str, stat: str, qualifier: ["qualified", "noMin"] = "noMin", year: int | None = None, team_substr: str | None = None) -> float | None

    Get a batting stat for a player from the selected dataset, optionally filtered by year and team. If multiple rows match, returns the sum.

    :param player_name: Player's full name.
    :param stat: Column name (case-insensitive), ex. "hr", "rbi", "obp", "ops".
    :param qualifier: "qualified" or "noMin" dataset (default "noMin").
    :param year: Optional year filter.
    :param team_substr: Optional case-insensitive team substring match.
    :return: Float value or None if not found.

.. py:function:: pitching_stat(player_name: str, stat: str, qualifier: ["qualified", "noMin"] = "noMin", year: int | None = None, team_substr: str | None = None) -> float | None

    Get a pitching stat for a player from the selected dataset, optionally filtered by year and team. If multiple rows match, returns the sum.

    :param player_name: Player's full name.
    :param stat: Column name (case-insensitive), ex. "era", "whip", "so", "bb", "ip".
    :param qualifier: "qualified" or "noMin" dataset (default "noMin").
    :param year: Optional year filter.
    :param team_substr: Optional case-insensitive team substring match.
    :return: Float value or None if not found.

.. py:function:: list_batters(qualifier: ["qualified", "noMin"] = "noMin", year: int | None = None, team_substr: str | None = None) -> list[str]

    List batter names from the selected dataset, optionally filtered by year and team substring.

    :param qualifier: "qualified" or "noMin" dataset (default "noMin").
    :param year: Optional year filter.
    :param team_substr: Optional case-insensitive team substring match.
    :return: Sorted list of batter names.

.. py:function:: list_pitchers(qualifier: ["qualified", "noMin"] = "noMin", year: int | None = None, team_substr: str | None = None) -> list[str]

    List pitcher names from the selected dataset, optionally filtered by year and team substring.

    :param qualifier: "qualified" or "noMin" dataset (default "noMin").
    :param year: Optional year filter.
    :param team_substr: Optional case-insensitive team substring match.
    :return: Sorted list of pitcher names.

Usage Examples
--------------

.. code-block:: python

    from ncaa_bbStats import (
        list_available_years,
        list_batters,
        top_players,
        batting_stat,
        get_player_rows,
    )

    # Discover latest year available for batting (qualified)
    years = list_available_years("batting", "qualified")
    latest = years[-1]

    # List a few batter names in the latest year (noMin)
    batters = list_batters("noMin", year=latest)

    # Top 5 HR leaders (qualified) in the latest year
    leaders = top_players("batting", "hr", n=5, year=latest)

    # Get a player's HR total (noMin) for the latest year
    if batters:
        hr_total = batting_stat(batters[0], "hr", qualifier="noMin", year=latest)

    # Fetch a player's row(s) with a few selected columns
    rows = get_player_rows("batting", "noMin", batters[0], year=latest, include_columns=["name", "team", "year", "hr"])


See Also
--------

- :doc:`player_names`
- :doc:`player_reference`
