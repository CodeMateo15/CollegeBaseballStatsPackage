Season Stats Reference
======================

This page lists all available season statistics, their abbreviations (as used in function calls), and descriptions.

Stats List
----------

- **W**: Wins  
  Number of games won by the team.
- **L**: Losses  
  Number of games lost.
- **T**: Ties  
  Number of games ending in a tie.
- **WPCT**: Winning Percentage  
  Ratio of wins to total games played.
- **G**: Games Played  
  Total number of games participated in.
- **BB (Batting)**: Walks (Batting)  
  Times a batter reaches base via balls.
- **AB**: At Bats  
  Number of official batting attempts.
- **H**: Hits  
  Times a batter safely reaches base via a hit.
- **BA**: Batting Average  
  Hits divided by at bats.
- **DP**: Double Plays Turned  
  Number of double plays completed by defense.
- **DPPG**: Double Plays Per Game  
  Average double plays per game.
- **2B**: Doubles  
  Hits where the batter reaches second base.
- **2BPG**: Doubles Per Game  
  Average doubles per game.
- **IP**: Innings Pitched  
  Total innings thrown by a pitcher.
- **R (Pitching)**: Runs Allowed (Pitching)  
  Runs given up by a pitcher.
- **ER**: Earned Runs  
  Runs scored without defensive errors.
- **ERA**: Earned Run Average  
  Earned runs per nine innings pitched.
- **PO**: Putouts  
  Defensive outs recorded by a player.
- **A**: Assists  
  Defensive plays leading to an out.
- **E**: Errors  
  Defensive mistakes allowing runners to advance.
- **FPCT**: Fielding Percentage  
  Ratio of successful plays to total chances.
- **HB**: Hit Batters (Pitching)  
  Batters hit by a pitch thrown.
- **HBP**: Hit By Pitch (Batting)  
  Times a batter is hit by a pitch.
- **HA**: Hits Allowed (Pitching)  
  Hits given up by a pitcher.
- **HAPG**: Hits Allowed Per Game  
  Average hits allowed per game.
- **HR**: Home Runs  
  Hits resulting in the batter scoring without error.
- **HRPG**: Home Runs Per Game  
  Average home runs per game.
- **SF**: Sacrifice Flies  
  Fly balls allowing a runner to score.
- **SH**: Sacrifice Hits  
  Bunts advancing runners at the cost of an out.
- **OBP**: On-Base Percentage  
  Times reached base divided by plate appearances.
- **SB**: Stolen Bases  
  Bases advanced without a hit or error.
- **CS**: Caught Stealing  
  Times a runner is thrown out attempting to steal.
- **R (Batting)**: Runs Scored (Batting)  
  Runs scored by a batter.
- **RPG**: Runs Per Game  
  Average runs scored per game.
- **SHO**: Shutouts  
  Games with no runs allowed.
- **TB**: Total Bases  
  Sum of all bases gained from hits.
- **SLG**: Slugging Percentage  
  Total bases divided by at bats.
- **SBPG**: Stolen Bases Per Game  
  Average stolen bases per game.
- **SO**: Strikeouts (Batting)  
  Times a batter is retired via strikes.
- **BB (Pitching)**: Walks Allowed (Pitching)  
  Walks issued by a pitcher.
- **K/BB**: Strikeout-to-Walk Ratio (Pitching)  
  Strikeouts divided by walks allowed.
- **K/9**: Strikeouts Per 9 Innings (Pitching)  
  Strikeouts per nine innings pitched.
- **3B**: Triples  
  Hits where the batter reaches third base.
- **3BPG**: Triples Per Game  
  Average triples per game.
- **WHIP**: Walks and Hits Per Inning Pitched  
  Walks plus hits divided by innings pitched.
- **BBPG (Pitching)**: Walks Per Game (Pitching)  
  Average walks allowed per game.


Usage
-----

Use the abbreviations in function calls, example:

.. code-block:: python

    get_team_stat("HR", "Northeastern", 2024, 1)
    average_team_stat_float("ERA", "Northeastern", 1, 2010, 2024)
