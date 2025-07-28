Draft Module
============

The `draft` module provides functions for accessing and displaying MLB and college baseball draft data for teams and players.

Functions
---------

.. py:function:: parse_mlb_draft(year: int) -> list[dict]:

    Parses MLB draft results from Baseball Almanac for a given year (1965–2025).

    :param year: Year of the draft.
    :return: List of drafted player details.


.. py:function:: get_drafted_players_mlb(team_name: str, year: int) -> list:

    Retrieves a list of players from the specified team drafted to MLB in a given year.

    :param team_name: Name or substring of the team.
    :param year: Year of the draft.
    :return: List of drafted player details.


.. py:function:: get_drafted_players_all_years_mlb(team_name: str) -> list:

    Retrieves all MLB draft picks for a team across all available years.

    :param team_name: Name or substring of the team.
    :return: List of drafted player details.


.. py:function:: get_drafted_players_college(team_name: str, year: int) -> list:

    Retrieves a list of players from the specified team drafted to college in a given year.

    :param team_name: Name or substring of the team.
    :param year: Year of the draft.
    :return: List of drafted player details.


.. py:function:: get_drafted_players_all_years_college(team_name: str) -> list:

    Retrieves all college draft picks for a team across all available years.

    :param team_name: Name or substring of the team.
    :return: List of drafted player details.


.. py:function:: print_draft_picks_mlb(picks: list) -> None

   Prints formatted draft pick info from a list of draft dicts for MLB teams.

   :param picks: List of dictionaries, each representing an MLB draft pick with fields like "Year", "Round", "Pick", "Player Name", "POS", and "Drafted From".
   :return: None. Prints draft picks to the console.


.. py:function:: print_draft_picks_college(picks: list) -> None

   Prints formatted draft pick info from a list of draft dicts for college teams.

   :param picks: List of dictionaries, each representing a college draft pick with fields like "Year", "Round", "Pick", "Player Name", "POS", and "Drafted By".
   :return: None. Prints draft picks to the console.


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
- :doc:`team_names_mlb`
