Draft Module
============

The `draft` module provides functions for accessing and displaying MLB and college baseball draft data for teams and players.

Functions
---------

.. py:function:: parse_mlb_draft(year: int) -> list[dict]:

    Parses MLB draft results from Baseball Almanac for a given year (1965–2025).

    :param year: Year of the draft.
    :return: List of drafted player details.


.. py:function:: get_drafted_players_mlb(team_name: str, year: int, division: int) -> list:

    Retrieves a list of players from the specified team drafted to MLB in a given year and division.

    :param team_name: Name or substring of the team.
    :param year: Year of the draft.
    :param division: NCAA division number.
    :return: List of drafted player details.


.. py:function:: get_drafted_players_all_years_mlb(team_name: str, division: int) -> dict:

    Retrieves all MLB draft picks for a team across all available years in a division.

    :param team_name: Name or substring of the team.
    :param division: NCAA division number.
    :return: Dictionary mapping years to lists of drafted players.


.. py:function:: get_drafted_players_college(team_name: str, year: int, division: int) -> list:

    Retrieves a list of players from the specified team drafted to college in a given year and division.

    :param team_name: Name or substring of the team.
    :param year: Year of the draft.
    :param division: NCAA division number.
    :return: List of drafted player details.


.. py:function:: get_drafted_players_all_years_college(team_name: str, division: int) -> dict:

    Retrieves all college draft picks for a team across all available years in a division.

    :param team_name: Name or substring of the team.
    :param division: NCAA division number.
    :return: Dictionary mapping years to lists of drafted players.


.. py:function:: print_draft_picks_mlb(team_name: str, year: int, division: int) -> None:

    Prints MLB draft picks for a team in a given year and division in a readable format.

    :param team_name: Name or substring of the team.
    :param year: Year of the draft.
    :param division: NCAA division number.
    :return: None. Prints results to the console.


.. py:function:: print_draft_picks_college(team_name: str, year: int, division: int) -> None:

    Prints college draft picks for a team in a given year and division in a readable format.

    :param team_name: Name or substring of the team.
    :param year: Year of the draft.
    :param division: NCAA division number.
    :return: None. Prints results to the console.


Usage Example
-------------

.. code-block:: python

    from ncaa_bbStats import get_drafted_players_college, get_drafted_players_all_years_college

    # Example: All Northeastern draftees in the 2025 draft:
    northeastern_2025 = get_drafted_players_college("Northeastern University", 2025)
    print_draft_picks_college(northeastern_2025)

    # Example: All Northeastern draftees since 1965:
    northeastern_all = get_drafted_players_all_years_college("Northeastern University")
    print(f"\nTotal picks from Northeastern: {len(northeastern_all)}")

.. code-block:: python

    from ncaa_bbStats import parse_mlb_draft

    draft_2025 = parse_mlb_draft(2025)

    # Print the top 5 picks
    for pick in draft_2025[:5]:
        print(pick)

Data Source
-----------

Team statistics are loaded from cached JSON files located in:

    src/data/mlb_draft_cache/YYY.json

where `YYYY` is the year.

See Also
--------

- :doc:`team_stats`
