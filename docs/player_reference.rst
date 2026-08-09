Player Stats Reference
======================

This page lists all available player statistics, their abbreviations (as used in function calls), and descriptions.

.. note::

   qualified vs noMin

   qualified means a batter reached 2 plate appearances per team game and a
   pitcher 0.7 innings per team game. Over a full 56-game season that is about
   112 plate appearances or 39 innings, but the bar moves with the team's own
   schedule -- a team that played 52 games sets a lower one, and the shortened
   2021 season lower still.

   These are below the Major League conventions (3.1 PA/G, 1 IP/G) because
   college seasons are shorter and pitching staffs deeper; the MLB cuts would
   leave very few qualifiers. Call ``qualification_rules()`` for the configured
   minimum together with the smallest qualifying total actually present in the
   data.

   noMin means there's no filter for amount of plate appearances or innings pitched.

   Both live in one file, distinguished by a ``qualified`` column. Pass
   ``qualifier="qualified"`` or ``"noMin"`` exactly as before.

.. note::

   **Only counting statistics are stored.** Every rate and advanced statistic on
   this page is computed when you read it, from the counting stats plus league
   constants this package derives from its own NCAA team-stats cache. Both ship,
   so nothing is lost -- the arithmetic rates reproduce exactly.

   Metrics prefixed ``c`` (``cwoba``, ``cwrc+``, ``cfip``, ...) are the
   college-calibrated analogues of the familiar sabermetric statistics. They are
   built the same way, but their league constants come from NCAA play rather
   than from Major League Baseball or a vendor's proprietary values, so the
   numbers are close to but not interchangeable with same-named statistics
   published elsewhere. See :doc:`data_provenance` for the formulas, the
   estimation method, and measured correlations.

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

- **cspd**: Speed Score

  Composite baserunning speed metric on a 0-10 scale, averaging stolen-base
  success rate, attempt frequency, triples rate, and runs scored per time on
  base. Its constants were fitted to Major League play, so NCAA hitters center
  near 3.9 rather than the conventional 5.0 -- compare players to each other,
  not to the usual scale. Informational only.

- **babip**: Batting Average on Balls In Play

  Batting average on non-HR balls put in play.

- **cwsb**: Stolen Base Runs

  Runs above or below average from stolen bases and times caught stealing,
  measured against what a league-average runner would produce from the same
  number of times on base.

- **cwrc**: Weighted Runs Created

  Total runs the hitter is responsible for producing.

- **cwraa**: Weighted Runs Above Average

  Runs contributed above a league-average hitter. Zero is exactly average.

- **cwoba**: Weighted On-Base Average

  One number for a hitter's total offensive value per plate appearance,
  weighting each way of reaching base by how many runs it is actually worth in
  NCAA play. Unlike OBP it distinguishes a walk from a home run; unlike SLG it
  weights by run value rather than total bases. Scaled so the league average
  equals league OBP.

- **cwrc+**: Weighted Runs Created Plus

  Weighted Runs Created indexed so 100 is league average: 130 is 30% better than
  an average hitter that season, 70 is 30% worse. Because it is indexed to its
  own season, it compares hitters across different run environments. No park
  adjustment is applied -- see :doc:`data_provenance`.

Pitching Stats List
-------------------

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

- **clob%**: Left On Base Percentage

  Share of baserunners the pitcher stranded. Regresses hard toward the league
  mean, so a large deviation usually predicts a move back toward average rather
  than a repeatable skill.

- **cfip**: Fielding Independent Pitching

  Judges a pitcher only on the outcomes that do not depend on the defence behind
  them -- strikeouts, walks, hit batters and home runs -- and puts the result on
  the ERA scale. A pitcher whose ERA sits well above their cFIP was probably let
  down by their defence or by sequencing luck, and the reverse.

- **e-cf**: ERA minus cFIP

  Difference between Earned Run Average and Fielding Independent Pitching.
  Strongly positive suggests the pitcher was let down by defence or sequencing;
  strongly negative suggests they were helped.

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
