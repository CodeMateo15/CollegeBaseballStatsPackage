Season Stats Reference
======================

This page lists all available season statistics, their abbreviations (as used in function calls), and descriptions.

Stats List
----------

- **W**: Wins (2002 - 2025)

  Number of games won by the team.

- **L**: Losses (2002 - 2025)

  Number of games lost.

- **T**: Ties (2002 - 2025)

  Number of games ending in a tie.

- **WPCT**: Winning Percentage (2011 - 2025)

  Ratio of wins to total games played.

- **G**: Games Played (2002 - 2025)

  Total number of games participated in.

- **BB (Batting)**: Walks Batting (2008 - 2025)

  Times a batter reaches base via balls.

- **AB**: At Bats (2002 - 2025)

  Number of official batting attempts.

- **H**: Hits (2002 - 2025)

  Times a batter safely reaches base via a hit.

- **BA**: Batting Average (2002 - 2025)

  Hits divided by at bats.

- **DP**: Double Plays Turned (2008 - 2025)

  Number of double plays completed by defense.

- **DPPG**: Double Plays Per Game (2003 - 2025)
  
  Average double plays per game.

- **2B**: Doubles (2008 - 2025)

  Hits where the batter reaches second base.

- **2BPG**: Doubles Per Game (2002 - 2025)

  Average doubles per game.

- **IP**: Innings Pitched (2002 - 2025)

  Total innings thrown by a pitcher.

- **R (Pitching)**: Runs Allowed Pitched (2002 - 2025)

  Runs given up by a pitcher.

- **ER**: Earned Runs (2002 - 2025)

  Runs scored without defensive errors.

- **ERA**: Earned Run Average (2002 - 2025)

  Earned runs per nine innings pitched.

- **PO**: Putouts (2002 - 2025)

  Defensive outs recorded by a player.

- **A**: Assists (2002 - 2025)

  Defensive plays leading to an out.

- **E**: Errors (2002 - 2025)
  
  Defensive mistakes allowing runners to advance.

- **FPCT**: Fielding Percentage (2002 - 2025)

  Ratio of successful plays to total chances.

- **HB**: Hit Batters Pitched (2013 - 2025)

  Batters hit by a pitch thrown.

- **HBP**: Hit By Pitch Batting (2008 - 2025)

  Times a batter is hit by a pitch.

- **HA**: Hits Allowed Pitched (2008 - 2025) 

  Hits given up by a pitcher.

- **HAPG**: Hits Allowed Per Game (2008 - 2025)

  Average hits allowed per game.

- **HR**: Home Runs (2008 - 2025)

  Hits resulting in the batter scoring without error.

- **HRPG**: Home Runs Per Game (2002 - 2025) 

  Average home runs per game.

- **SF**: Sacrifice Flies (2008 - 2025) 

  Fly balls allowing a runner to score.

- **SH**: Sacrifice Hits (2008 - 2025)

  Bunts advancing runners at the cost of an out.

- **OBP**: On-Base Percentage (2012 - 2025)

  Times reached base divided by plate appearances.

- **SB**: Stolen Bases (2002 - 2025)

  Bases advanced without a hit or error.

- **SBPG**: Stolen Bases Per Game (2008 - 2025)

  Average stolen bases per game.

- **CS**: Caught Stealing (2002 - 2025)

  Times a runner is thrown out attempting to steal.

- **R (Batting)**: Runs Scored Batting (2008 - 2025)

  Runs scored by a batter.

- **RPG**: Runs Per Game (2002 - 2025)

  Average runs scored per game.

- **SHO**: Shutouts (2013 - 2025)

  Games with no runs allowed.

- **TB**: Total Bases (2003 - 2025)

  Sum of all bases gained from hits.

- **SLG**: Slugging Percentage (2003 - 2025)

  Total bases divided by at bats.

- **SO**: Strikeouts (Batting) (2012 - 2025)

  Times a batter is retired via strikes.

- **BB (Pitching)**: Walks Allowed Pitched (2012 - 2025)

  Walks issued by a pitcher.

- **K/BB**: Strikeout-to-Walk Ratio Pitched (2012 - 2025)

  Strikeouts divided by walks allowed.

- **K/9**: Strikeouts Per 9 Innings Pitched (2008 - 2025)

  Strikeouts per nine innings pitched.

- **TP**: Triple Plays (2013 - 2025)

  The defending team records three outs on a single defensive play.

- **3B**: Triples (2008 - 2025)

  Hits where the batter reaches third base.

- **3BPG**: Triples Per Game (2002 - 2025)

  Average triples per game.

- **WHIP**: Walks and Hits Per Inning Pitched (2012 - 2025)

  Walks plus hits divided by innings pitched.

- **BBPG (Pitching)**: Walks Per Game Pitched (2011 - 2025)

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
