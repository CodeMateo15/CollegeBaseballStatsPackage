Season Stats Reference
======================

.. note::

   The year range beside each statistic is the span in which the NCAA actually
   published it, read from the shipped cache rather than maintained by hand --
   ``tests/test_docs.py`` fails if the two disagree. Coverage varies by
   statistic because the NCAA added categories over time, and by division:
   Division II has never reported SH, HB, or OBP.

This page lists all available season statistics, their abbreviations (as used in function calls), and descriptions.

Stats List
----------

- **W**: Wins (2002 - 2026)

  Number of games won by the team.

- **L**: Losses (2002 - 2026)

  Number of games lost.

- **T**: Ties (2002 - 2026)

  Number of games ending in a tie.

- **WPCT**: Winning Percentage (2011 - 2026)

  Ratio of wins to total games played.

- **G**: Games Played (2002 - 2026)

  Total number of games participated in.

- **BB (Batting)**: Walks Batting (2008 - 2026)

  Times a batter reaches base via balls.

- **AB**: At Bats (2002 - 2026)

  Number of official batting attempts.

- **H**: Hits (2002 - 2026)

  Times a batter safely reaches base via a hit.

- **BA**: Batting Average (2002 - 2026)

  Hits divided by at bats.

- **DP**: Double Plays Turned (2003 - 2026)

  Number of double plays completed by defense.

- **DPPG**: Double Plays Per Game (2003 - 2026)
  
  Average double plays per game.

- **2B**: Doubles (2003 - 2026)

  Hits where the batter reaches second base.

- **2BPG**: Doubles Per Game (2003 - 2026)

  Average doubles per game.

- **IP**: Innings Pitched (2002 - 2026)

  Total innings thrown by a pitcher.

- **R (Pitching)**: Runs Allowed Pitched (2002 - 2026)

  Runs given up by a pitcher.

- **ER**: Earned Runs (2002 - 2026)

  Runs scored without defensive errors.

- **ERA**: Earned Run Average (2002 - 2026)

  Earned runs per nine innings pitched.

- **PO**: Putouts (2002 - 2026)

  Defensive outs recorded by a player.

- **A**: Assists (2002 - 2026)

  Defensive plays leading to an out.

- **E**: Errors (2002 - 2026)
  
  Defensive mistakes allowing runners to advance.

- **FPCT**: Fielding Percentage (2002 - 2026)

  Ratio of successful plays to total chances.

- **HB**: Hit Batters Pitched (2013 - 2026)

  Batters hit by a pitch thrown.

- **HBP**: Hit By Pitch Batting (2008 - 2026)

  Times a batter is hit by a pitch.

- **HA**: Hits Allowed Pitched (2008 - 2026) 

  Hits given up by a pitcher.

- **HAPG**: Hits Allowed Per Game (2008 - 2026)

  Average hits allowed per game.

- **HR**: Home Runs (2003 - 2026)

  Hits resulting in the batter scoring without error.

- **HRPG**: Home Runs Per Game (2003 - 2026) 

  Average home runs per game.

- **SF**: Sacrifice Flies (2008 - 2026) 

  Fly balls allowing a runner to score.

- **SH**: Sacrifice Hits (2012 - 2026)

  Bunts advancing runners at the cost of an out.

- **OBP**: On-Base Percentage (2012 - 2026)

  Times reached base divided by plate appearances.

- **SB**: Stolen Bases (2008 - 2026)

  Bases advanced without a hit or error.

- **SBPG**: Stolen Bases Per Game (2008 - 2026)

  Average stolen bases per game.

- **CS**: Caught Stealing (2008 - 2026)

  Times a runner is thrown out attempting to steal.

- **R (Batting)**: Runs Scored Batting (2002 - 2026)

  Runs scored by a batter.

- **RPG**: Runs Per Game (2002 - 2026)

  Average runs scored per game.

- **SHO**: Shutouts (2014 - 2026)

  Games with no runs allowed.

- **TB**: Total Bases (2003 - 2026)

  Sum of all bases gained from hits.

- **SLG**: Slugging Percentage (2003 - 2026)

  Total bases divided by at bats.

- **SO**: Strikeouts (Batting) (2008 - 2026)

  Times a batter is retired via strikes.

- **BB (Pitching)**: Walks Allowed Pitched (2011 - 2026)

  Walks issued by a pitcher.

- **K/BB**: Strikeout-to-Walk Ratio Pitched (2012 - 2026)

  Strikeouts divided by walks allowed.

- **K/9**: Strikeouts Per 9 Innings Pitched (2008 - 2026)

  Strikeouts per nine innings pitched.

- **TP**: Triple Plays (2013 - 2026)

  The defending team records three outs on a single defensive play.

- **3B**: Triples (2003 - 2026)

  Hits where the batter reaches third base.

- **3BPG**: Triples Per Game (2003 - 2026)

  Average triples per game.

- **WHIP**: Walks and Hits Per Inning Pitched (2012 - 2026)

  Walks plus hits divided by innings pitched.

- **BBPG (Pitching)**: Walks Per Game Pitched (2011 - 2026)

  Average walks allowed per game.


Usage
-----

Use the abbreviations in function calls, example:

.. code-block:: python

    get_team_stat("HR", "Northeastern", 2024, 1)
    average_team_stat_float("ERA", "Northeastern", 1, 2010, 2024)

See Also
--------

- :doc:`team_stats`
- :doc:`team_names_stats`
- :doc:`team_names_mlb`
