Team Registry
=============

One canonical id per program, across every data source.

Overview
--------

Each dataset spells schools its own way::

    NCAA team stats     "Eastern Ill. (MVC)"
    Player leaderboards "EIU"
    Draft records       "Eastern Illinois University"
    RPI                 "Eastern Illinois"

None of these join without a shared key. The registry gives every program one
``team_id`` and records each source's spelling as an alias, so all four land on
the same program::

    >>> from ncaa_bbStats import resolve_team
    >>> resolve_team("Eastern Ill.")
    'IPEDS:144892'
    >>> resolve_team("EIU") == resolve_team("Eastern Illinois")
    True

The id
------

Where a program's federal IPEDS unitid is known, the id is ``IPEDS:<unitid>``.
That identifier survives rebrands, so a renamed program keeps one id and one
continuous history::

    >>> resolve_team("Dixie State") == resolve_team("Utah Tech")
    True
    >>> resolve_team("Houston Baptist") == resolve_team("Houston Christian")
    True

Programs with no unitid on file get a minted ``NCAA:<slug>`` id, frozen on first
assignment. Currently 308 of 1,023 programs carry an IPEDS id; the rest are
Division II and III schools not yet crosswalked.

.. note::

   **Division is not part of identity.** A program that moves between divisions
   keeps one id; the division is recorded per season by :func:`team_seasons`.
   Utah Tech played Division II through 2020 and Division I from 2025, and both
   halves of that history sit under one id.

Matching
--------

Lookup is exact first, then against a folded form that absorbs the mechanical
differences between sources -- ``"Alabama St."`` and ``"Alabama State"``,
``"Ark.-Pine Bluff"`` and ``"Arkansas-Pine Bluff"``. Genuine naming
disagreements are handled by stored aliases.

**There is no fuzzy fallback.** An unrecognised name returns ``None`` rather
than the closest guess. Silent near-matching is how two programs get swapped
without anyone noticing, and the source data this registry was built from
contains exactly that failure: eleven acronyms pointed at the wrong school, so
one entry answered to both "Mercer" and "Merrimack". The build refuses to write
if any alias resolves to more than one program.

Functions
---------

.. py:function:: resolve_team(name: str, *, season: int | None = None, namespace: str | None = None, division: int | None = None) -> str | None

    Map any spelling of a team name to its canonical ``team_id``.

    :param name: A team or school name in any supported spelling.
    :param season: Restrict to aliases valid that season.
    :param namespace: Restrict to one source's spellings. See `Namespaces`_.
    :param division: Require the program to have played this division.
    :return: The ``team_id``, or None if unknown or ambiguous.

.. py:function:: resolve_team_verbose(name: str, *, season: int | None = None, namespace: str | None = None, division: int | None = None) -> Resolution | None

    Resolve a name, reporting how the match was made. The returned object has
    ``team_id``, ``matched_alias``, ``namespace``, and ``method`` (``"exact"`` or
    ``"normalized"``). Useful when auditing a join.

    :param name: A team or school name.
    :param season: Restrict to aliases valid that season.
    :param namespace: Restrict to one source's spellings.
    :param division: Require the program to have played this division.
    :return: A ``Resolution``, or None.

.. py:function:: team_info(team: str, season: int | None = None) -> dict | None

    Return a program's identity record: ``team_id``, ``canonical_name``,
    ``ipeds_unitid``, ``institution_name``, ``state``, ``id_source``,
    ``first_season``, ``last_season``, ``divisions``. With ``season``, also
    that season's ``division`` and ``conference``.

    :param team: A ``team_id`` or any known spelling.
    :param season: Season to include context for.
    :return: The record, or None if the team is unknown.

.. py:function:: team_aliases(team: str, namespace: str | None = None) -> list[str]

    Every known spelling of a program.

    :param team: A ``team_id`` or any known spelling.
    :param namespace: Restrict to one source.
    :return: Sorted unique spellings.

.. py:function:: team_seasons(team: str) -> list[dict]

    A program's season-by-season division and conference.

    :param team: A ``team_id`` or any known spelling.
    :return: One dict per season with ``season``, ``division``, ``conference``, ``ncaa_short``.

.. py:function:: team_division(team: str, season: int) -> int | None

    Which division a program played in a season.

    :param team: A ``team_id`` or any known spelling.
    :param season: Season year.
    :return: 1, 2, or 3, or None if there is no record that season.

.. py:function:: team_conference(team: str, season: int) -> str | None

    Which conference a program played in a season.

    :param team: A ``team_id`` or any known spelling.
    :param season: Season year.
    :return: The conference code, or None.

.. py:function:: list_teams(season: int | None = None, division: int | None = None, conference: str | None = None) -> list[dict]

    List programs, optionally filtered.

    :param season: Only programs with a record that season.
    :param division: Only programs in this division.
    :param conference: Only programs in this conference (case-insensitive).
    :return: Identity records sorted by canonical name.

.. py:function:: list_conferences(season: int, division: int | None = None) -> list[str]

    List the conferences active in a season.

    :param season: Season year.
    :param division: Restrict to one division.
    :return: Sorted conference codes.

.. py:function:: crosswalk(from_namespace: str, to_namespace: str, season: int | None = None) -> dict

    Map one source's spellings directly onto another's, for bulk joins.

    :param from_namespace: Source namespace.
    :param to_namespace: Target namespace.
    :param season: Restrict to aliases valid that season.
    :return: ``{from_spelling: to_spelling}``, omitting entries with no counterpart.

Namespaces
----------

One per source, kept separate so a wrong alias in one cannot affect lookups
against another.

- ``ncaa_short`` -- NCAA team stats, e.g. ``"Eastern Ill."``
- ``ncaa_label`` -- NCAA team stats with conference, e.g. ``"Eastern Ill. (MVC)"``
- ``fg_acronym`` -- player leaderboards, e.g. ``"EIU"``
- ``fg_full`` -- player leaderboards, full name
- ``rpi`` -- Warren Nolan
- ``eada_institution`` -- IPEDS charter name
- ``almanac_school`` -- Baseball Almanac draft records

Usage
-----

.. code-block:: python

    from ncaa_bbStats import (
        resolve_team, team_info, team_seasons, list_teams, crosswalk,
    )

    # Join a player row to a team stats row
    team_id = resolve_team("AUB")                 # player cache acronym
    info = team_info(team_id, season=2025)
    print(info["canonical_name"], info["conference"])   # Auburn SEC

    # Follow a program through a division change
    for s in team_seasons("Utah Tech"):
        print(s["season"], s["division"], s["conference"])

    # Everyone in a conference
    [t["canonical_name"] for t in list_teams(season=2025, conference="SEC")]

    # Bulk-map the player cache onto RPI spellings
    acronym_to_rpi = crosswalk("fg_acronym", "rpi", season=2025)

Data Source
-----------

``src/data/registry/`` -- ``teams.csv``, ``team_aliases.csv``,
``team_seasons.csv``. Built by ``tools/build_team_registry.py``.

See Also
--------

- :doc:`team_stats`
- :doc:`team_names_stats`
- :doc:`data_provenance`
