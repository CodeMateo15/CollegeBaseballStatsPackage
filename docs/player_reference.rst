Player Stats Reference
======================

This page lists all available player statistics, their abbreviations (as used in function calls), and descriptions.

.. note::

   qualified vs noMin

   qualified means a batter needs 3.1 plate appearances per game and a pitcher needs 1 inning pitched per game. 56 regular-season games, so batters need 174 plate appearances and pitchers need 56 innings pitched.

   noMin means there's no filter for amount of plate appearances or innings pitched.

Batting Stats List
------------------

- **g**: Games

  Total games played.

- **ab**: At-Bats

  Official batting attempts, excluding walks and sacrifices.

- **pa**: Plate Appearances

  Trips to the plate including AB, BB, HBP, SF, SH, etc.

- **h**: Hits

  Total hits recorded.

- **1b**: Singles

  One-base hits.

- **2b**: Doubles

  Two-base hits.

- **3b**: Triples

  Three-base hits.

- **hr**: Home Runs

  Hits resulting in the batter scoring.

- **r**: Runs

  Runs scored by the player.

- **rbi**: Runs Batted In

  Runs driven in by the player.

- **bb**: Walks

  Times reaching base via balls.

- **so**: Strikeouts

  Times retired on strikes.

- **hbp**: Hit By Pitch

  Times hit by a pitch.

- **sf**: Sacrifice Flies

  Fly-ball outs that score a runner.

- **sh**: Sacrifice Hits

  Bunts that advance runners at the cost of an out.

- **gdp**: Grounded Into Double Play

  Times grounding into a double play.

- **sb**: Stolen Bases

  Successful steals of a base.

- **cs**: Caught Stealing

  Times thrown out attempting to steal.

- **avg**: Batting Average

  Hits divided by at-bats.

- **bb%**: Walk Rate

  Walks divided by plate appearances.

- **k%**: Strikeout Rate

  Strikeouts divided by plate appearances.

- **bb/k**: Walk-to-Strikeout Ratio

  Walks divided by strikeouts.

- **obp**: On-Base Percentage

  Times reached base divided by plate appearances.

- **slg**: Slugging Percentage

  Total bases divided by at-bats.

- **ops**: On-Base Plus Slugging

  On-Base Percentage plus Slugging Percentage.

- **iso**: Isolated Power

  Slugging Percentage minus Batting Average.

- **spd**: Speed Score

  Composite baserunning speed metric.

- **babip**: Batting Average on Balls In Play

  Batting average on non-HR balls put in play.

- **wsb**: Weighted Stolen Base Runs

  Runs above/below average from Stolen Bases/Caught Stealing.

- **wrc**: Weighted Runs Created

  Estimated runs created.

- **wraa**: Weighted Runs Above Average

  Runs above league average from offense.

- **woba**: Weighted On-Base Average

  Weighted measure of overall offensive value.

- **wrc+**: Weighted Runs Created Plus

  Weighted Runs Created scaled to league and park (100 = average).

Pitching Stats List
------------------

- **w**: Wins

  Games credited as wins to the pitcher.

- **l**: Losses

  Games credited as losses to the pitcher.

- **era**: Earned Run Average

  Earned runs allowed per nine innings.

- **g**: Games

  Pitching appearances.

- **gs**: Games Started

  Starts made by the pitcher.

- **cg**: Complete Games

  Games pitched from start to finish.

- **sho**: Shutouts

  Complete games with zero runs allowed.

- **sv**: Saves

  Games finished while preserving a lead.

- **ip**: Innings Pitched

  Total innings thrown (with .1 = 1/3, .2 = 2/3).

- **tbf**: Batters Faced

  Total plate appearances against the pitcher.

- **h**: Hits

  Hits allowed.

- **r**: Runs

  Runs allowed (earned and unearned).

- **er**: Earned Runs

  Earned runs allowed.

- **hr**: Home Runs

  Home runs allowed.

- **bb**: Walks

  Walks issued.

- **hbp**: Hit Batters

  Batters hit by pitch.

- **wp**: Wild Pitches

  Pitches allowing runners to advance.

- **bk**: Balks

  Illegal pitching motions advancing runners.

- **so**: Strikeouts

  Batters struck out.

- **k/9**: Strikeouts per 9

  Strikeouts per nine innings.

- **bb/9**: Walks per 9

  Walks per nine innings.

- **k/bb**: Strikeout-to-Walk Ratio

  Strikeouts divided by walks.

- **hr/9**: Home Runs per 9

  Home runs allowed per nine innings.

- **k%**: Strikeout Rate

  Strikeouts divided by batters faced.

- **bb%**: Walk Rate

  Walks divided by batters faced.

- **k-bb%**: K-BB Rate

  Strikeout rate minus walk rate.

- **avg**: Batting Average Against

  Hits allowed divided by at-bats against.

- **whip**: Walks plus Hits per Inning Pitched

  (BB + H) divided by innings pitched.

- **babip**: Batting Average on Balls In Play Against

  Average on non-Home Run balls put in play against the pitcher.

- **lob%**: Left On Base Percentage

  Percentage of baserunners stranded.

- **fip**: Fielding Independent Pitching

  Run estimator based on HR, BB, HBP, SO, and IP.

- **e-f**: ERA minus FIP

  Difference between Earned Run Average and Fielding Independent Pitching.

Usage
-----

Use the abbreviations in function calls, example:

.. code-block:: python

    print(pitching_stat("Aiven Cabral", "era", "noMin", 2025))
    print(top_players("batting", "hr", 10, 2025))

See Also
--------

- :doc:`player_stats`
- :doc:`player_names`
