Player Names for Player Stats
=============================

An index of every player-season in the package, covering NCAA Division I from
2021 through 2025. Used by the Player Stats module.

Each entry includes:

- The ``name`` of the player
- The ``team`` acronym and full ``team name``
- The ``division``
- The ``year`` of the season
- ``qualified``, whether the player met that season's playing-time minimum

Download
--------

:download:`batting_players.csv <_static/data/player_stats/batting_players.csv>`

:download:`pitching_players.csv <_static/data/player_stats/pitching_players.csv>`

.. note::

   A player appears once per season played, so names repeat across years. A
   player who transferred mid-career appears under each team.

.. note::

   These replace the earlier ``*DOC.csv`` files, which were split by qualifier
   and carried an ``age`` column. Qualification is now a column rather than a
   separate file -- see :doc:`player_stats`. The files are regenerated from
   ``src/data/`` by ``docs/make_static_data.py``, and
   ``_static/data/MANIFEST.txt`` records the source hash of each.

See Also
--------

- :doc:`player_reference`
- :doc:`player_stats`
- :doc:`data_provenance`
