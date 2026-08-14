"""Generate the demonstration notebooks, one cell per group of functions.

    python notebooks/build_notebooks.py            # write, then execute
    python notebooks/build_notebooks.py --no-exec  # write only

Every public function in ``ncaa_bbStats.__all__`` appears in exactly one
notebook; ``tests/test_notebooks.py`` fails if one is added and not covered.

Generated rather than hand-edited so they can be re-run against a new release
without anyone reconciling 100-odd cells by hand. Edit this file, not the
``.ipynb``.
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))


def md(text):
    return {"cell_type": "markdown", "metadata": {},
            "source": text.strip().splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.strip().splitlines(keepends=True)}


NOTEBOOKS = {}


# ---------------------------------------------------------------- team stats
NOTEBOOKS["01_team_stats.ipynb"] = [
    md("""
# Team Stats, Registry, and Pythagorean Expectation

NCAA team statistics for Divisions I-III, 2002-2026, the canonical team
registry that lets every dataset join, and the Pythagorean expectation built on
top of them.

Covers: `get_team_stat`, `display_specific_team_stat`, `display_team_stats`,
`list_all_teams`, `plot_team_stat_over_years`, `average_all_team_stats`,
`average_team_stat_str`, `average_team_stat_float`, `resolve_team`,
`resolve_team_verbose`, `team_info`, `team_aliases`, `team_seasons`,
`team_division`, `team_conference`, `list_teams`, `list_conferences`,
`crosswalk`, `get_pythagorean_expectation`, `compare_pythagorean_expectation`,
`pythagorean_exponent`, `conference_exponents`, `luck_rating`,
`luckiest_teams`, `unluckiest_teams`
"""),
    code("""
%matplotlib inline
from ncaa_bbStats import *
"""),
    md("## Reading a team's season"),
    code("""
# A single statistic
print("Northeastern 2025 HR:", get_team_stat("HR", "Northeastern", 2025, 1))
print("Northeastern 2025 ERA:", get_team_stat("ERA", "Northeastern", 2025, 1))

# Team names match on a case-insensitive substring
display_specific_team_stat("WPCT", "Northeastern", 2025, 1)
"""),
    code("""
# Everything the cache holds for one team
display_team_stats("Northeastern", 2025, 1)
"""),
    code("""
# Who is in a division that season? Labels are "Team Name (Conference)".
teams = list_all_teams(2025, 1)
print(f"{len(teams)} Division I teams in 2025")
print(teams[:5])

print(f"\\n{len(list_all_teams(2025, 2))} Division II, "
      f"{len(list_all_teams(2025, 3))} Division III")
"""),
    md("## League averages"),
    code("""
averages = average_all_team_stats(2025, 1)
print(f"{len(averages)} averaged statistics")
for key in ["BA", "ERA", "HR", "WHIP", "FPCT"]:
    print(f"  {key:6s} {averages[key]}")
"""),
    code("""
print(average_team_stat_str("HR", 2025, 1))
print("as a float:", average_team_stat_float("HR", 2025, 1))

# Division III plays in a different run environment
print(average_team_stat_str("ERA", 2025, 1))
print(average_team_stat_str("ERA", 2025, 3))
"""),
    md("## Plotting a statistic over time"),
    code("""
plot_team_stat_over_years("WPCT", "Tennessee", 1, 2015, 2026)
"""),
    md("""
## The team registry

Each source spells schools differently. The registry maps them all onto one
`team_id`, which is what lets the datasets join.
"""),
    code("""
# Four spellings, one program
for name in ["Eastern Ill.", "EIU", "Eastern Illinois", "Eastern Illinois University"]:
    print(f"  {name:32s} -> {resolve_team(name)}")
"""),
    code("""
# resolve_team_verbose says how the match was made
print(resolve_team_verbose("Alabama State"))
print(resolve_team_verbose("EIU"))

# There is no fuzzy fallback: an unknown name returns None rather than a guess
print("unknown ->", resolve_team("Not A Real School"))
"""),
    code("""
# Rebrands keep one identity, so a program's history stays joined
print("Dixie State == Utah Tech      :",
      resolve_team("Dixie State") == resolve_team("Utah Tech"))
print("Houston Baptist == Houston Christian:",
      resolve_team("Houston Baptist") == resolve_team("Houston Christian"))

# Schools distinguished only by state stay separate
print("Miami (OH) != Miami (FL)      :",
      resolve_team("Miami (OH)") != resolve_team("Miami (FL)"))
"""),
    code("""
import json
print(json.dumps(team_info("Northeastern", season=2025), indent=2))
"""),
    code("""
# Every known spelling of a program, or just one source's
print("all aliases:", team_aliases("Northeastern")[:8])
print("as the player cache spells it:", team_aliases("Northeastern", "fg_acronym"))
"""),
    code("""
# Division is a season attribute, not part of identity: Utah Tech moved up
for row in team_seasons("Utah Tech"):
    if row["season"] >= 2019:
        print(f"  {row['season']}  D{row['division']}  {row['conference']}")
"""),
    code("""
print("Utah Tech division in 2015:", team_division("Utah Tech", 2015))
print("Utah Tech division in 2026:", team_division("Utah Tech", 2026))
print("Northeastern conference 2025:", team_conference("Northeastern", 2025))
"""),
    code("""
sec = list_teams(season=2025, conference="SEC")
print(f"{len(sec)} SEC programs:", [t["canonical_name"] for t in sec][:8])

print(f"\\n{len(list_conferences(2025, 1))} Division I conferences in 2025")
print(list_conferences(2025, 1)[:10])
"""),
    code("""
# Bulk-map one source's spellings onto another's
mapping = crosswalk("fg_acronym", "rpi", season=2025)
print(f"{len(mapping)} acronym -> RPI-name mappings")
for acronym in ["AUB", "ALST", "LSU"]:
    print(f"  {acronym:6s} -> {mapping.get(acronym)}")
"""),
    md("""
## Pythagorean expectation

What a team's record *should* have been, given the runs it scored and allowed.
A team well above its expectation won more close games than its run
differential justifies, which historically does not repeat.
"""),
    code("""
print("Northeastern 2018 expected win%:",
      get_pythagorean_expectation("Northeastern", 2018, 1))
print(compare_pythagorean_expectation("Northeastern", 2018, 1))

# The exponent can be overridden
print("with exponent 2.0:",
      get_pythagorean_expectation("Northeastern", 2018, 1, exponent=2.0))
"""),
    code("""
# Conference-fitted exponents ship but are EXPERIMENTAL and not the default:
# none of the 31 differs from 1.83 at p < 0.05.
print("default exponent:", pythagorean_exponent())
print("SEC-fitted      :", pythagorean_exponent("SEC"))

rows = conference_exponents()
print(f"\\n{len(rows)} conferences fitted; "
      f"{sum(1 for r in rows if r['significant'] == 'yes')} statistically significant")
for row in rows[:5]:
    print(f"  {row['conference']:16s} exp {row['exponent']:.3f}  "
          f"p={row['p_value']:.3f}  significant={row['significant']}")
"""),
    code("""
print(luck_rating("Northeastern", 2025))
"""),
    code("""
print("Outperformed their run differential most, D-I 2025:")
for row in luckiest_teams(2025, n=5):
    print(f"  {row['team']:20s} {row['conference']:10s} "
          f"actual {row['actual_win_pct']:.3f} vs expected "
          f"{row['expected_win_pct']:.3f}  ({row['luck_wins']:+.1f} wins)")

print("\\nUnderperformed most:")
for row in unluckiest_teams(2025, n=5):
    print(f"  {row['team']:20s} {row['conference']:10s} "
          f"actual {row['actual_win_pct']:.3f} vs expected "
          f"{row['expected_win_pct']:.3f}  ({row['luck_wins']:+.1f} wins)")
"""),
]


# -------------------------------------------------------------- player stats
NOTEBOOKS["02_player_stats.ipynb"] = [
    md("""
# Player Stats, Advanced Metrics, and Leaderboards

Division I player seasons, 2021-2025.

**The cache stores counting statistics only.** Every rate and advanced
statistic is computed when you read it, from those counts plus league constants
this package derives from its own NCAA team data — so they can never fall out
of step with the data underneath.

Covers: `list_available_years`, `list_players`, `list_batters`, `list_pitchers`,
`player_seasons`, `batting_stat`, `pitching_stat`, `get_player_rows`,
`load_player_frame`, `top_players`, `leaderboard`, `stat_direction`,
`qualification_rules`, `cwoba`, `cwraa`, `cwrc`, `cwrc_plus`, `cwsb`, `cspd`,
`cfip`, `clob_pct`, `league_constants`, `seasons_with_constants`
"""),
    code("""
from ncaa_bbStats import *
"""),
    md("## Finding players"),
    code("""
print("batting seasons:", list_available_years("batting", "qualified"))
print("pitching seasons:", list_available_years("pitching", "qualified"))
"""),
    code("""
# qualified = met the playing-time minimum; noMin = everyone
print("2025 batters, no minimum:", len(list_batters(year=2025)))
print("2025 batters, qualified :", len(list_batters("qualified", year=2025)))
print("2025 pitchers, qualified:", len(list_pitchers("qualified", year=2025)))

# Narrow by team
print("\\nNortheastern batters 2025:", list_batters(year=2025, team_substr="NE")[:5])
"""),
    code("""
print(qualification_rules("batting", 2025))
print(qualification_rules("pitching", 2025))
"""),
    code("""
# list_players is the general form behind list_batters / list_pitchers
print(list_players("pitching", "qualified", year=2025)[:5])

print("\\nAiven Cabral pitched in:", player_seasons("pitching", "noMin", "Aiven Cabral"))
"""),
    md("## Reading a statistic"),
    code("""
# Counting stats
print("Jack Goodman 2025 HR:", batting_stat("Jack Goodman", "hr", year=2025))

# Rate stats are computed on read -- no column holds them
for stat in ["avg", "obp", "slg", "ops", "iso", "babip", "bb%", "k%"]:
    print(f"  {stat:6s} {batting_stat('Jack Goodman', stat, year=2025):.4f}")
"""),
    code("""
for stat in ["so", "era", "whip", "k/9", "bb/9", "k-bb%"]:
    print(f"  {stat:6s} {pitching_stat('Aiven Cabral', stat, year=2025):.4f}")
"""),
    md("""
### Multi-season figures are rebuilt, not averaged

Asking for a stat without a year aggregates the player's whole career.
Counting stats are summed; **rates are recomputed from the summed components**.
A pitcher who threw to a 3.00 ERA one year and 5.00 the next did not have an
8.00 ERA.
"""),
    code("""
rows = get_player_rows("pitching", "noMin", "Aiven Cabral",
                       include_columns=["year", "ip", "er", "era", "so"])
for row in rows:
    print(f"  {row['year']}  {row['ip']:>6} IP  {row['er']:>3} ER  ERA {row['era']:.2f}")

print(f"\\n  career IP  {pitching_stat('Aiven Cabral', 'ip')}  (true innings)")
print(f"  career ER  {pitching_stat('Aiven Cabral', 'er')}")
print(f"  career ERA {pitching_stat('Aiven Cabral', 'era'):.2f}  "
      f"<- 9 x ER / IP, not the mean of the three seasons")
"""),
    code("""
# The whole table, with every derived column attached
frame = load_player_frame("batting", "qualified")
print(frame.shape)
print(list(frame.columns))
"""),
    md("""
## Advanced metrics

Metrics prefixed `c` are college-calibrated: built the same way as the familiar
sabermetric statistics, but with league constants regressed from NCAA play
rather than borrowed from elsewhere.
"""),
    code("""
for stat in ["cwoba", "cwrc+", "cwraa", "cwrc", "cwsb", "cspd"]:
    print(f"  {stat:8s} {batting_stat('Jack Goodman', stat, year=2025):8.3f}")

print()
for stat in ["cfip", "clob%", "e-cf"]:
    print(f"  {stat:8s} {pitching_stat('Aiven Cabral', stat, year=2025):8.3f}")
"""),
    code("""
# The same metrics computed from a stat line directly
line = {"ab": 203, "h": 68, "2b": 17, "3b": 1, "hr": 10,
        "bb": 26, "hbp": 5, "sf": 0, "pa": 234, "so": 49, "sb": 9, "cs": 2, "r": 51}

print("cwoba    ", round(cwoba(line, 2025, division=1), 4))
print("cwraa    ", round(cwraa(line, 2025, division=1), 2))
print("cwrc     ", round(cwrc(line, 2025, division=1), 2))
print("cwrc_plus", round(cwrc_plus(line, 2025, division=1), 1))
print("cwsb     ", round(cwsb(line, 2025, division=1), 3))
print("cspd     ", round(cspd(line), 2))
"""),
    code("""
pitcher = {"ip": 89.1, "hr": 6, "bb": 29, "so": 74, "hbp": 6,
           "h": 63, "r": 34, "er": 29, "tbf": 361}
print("cfip    ", round(cfip(pitcher, 2025, division=1), 3))
print("clob_pct", round(clob_pct(pitcher), 4))
"""),
    md("""
### The constants behind them

Run values are regressed from the packaged NCAA team-stats cache, per season and
division. `cwrc_plus` applies **no park adjustment** — NCAA park data is not
public — so hitters at extreme-altitude programs are flattered.
"""),
    code("""
constants = league_constants(2025, division=1)
print("run values, D-I 2025:")
for event in ["1b", "2b", "3b", "hr", "bb", "hbp", "sb", "cs"]:
    print(f"  {event:4s} {constants['w_' + event]:+.3f}")
print(f"\\n  league OBP    {constants['lg_obp']:.4f}")
print(f"  league R/PA   {constants['lg_r_pa']:.4f}")
print(f"  park factor   {constants['park_factor']}  (not modelled)")
print(f"  fit R2        {constants['r2']}")
"""),
    code("""
pitching_constants = league_constants(2025, division=1, kind="pitching")
print(f"league ERA    {pitching_constants['lg_era']:.3f}")
print(f"cFIP constant {pitching_constants['cfip_constant']:.3f}")

# Seasons too sparse to fit return None rather than a fabricated number
print("\\nD-I seasons with constants:", seasons_with_constants(1))
print("D-III:", seasons_with_constants(3))
print("\\n2005 is too sparse ->", cwoba(line, 2005, division=1))
"""),
    md("""
## Leaderboards

`leaderboard` takes the sort direction from the statistic, so a top-ERA list
contains good pitchers. `top_players` is the older function and always sorts
descending.
"""),
    code("""
print("top_players sorts descending unconditionally:")
for row in top_players("pitching", "era", 3, 2025):
    print(f"  {row['name']:22s} {row['value']:.2f}   <- the WORST ERAs")

print("\\nleaderboard picks the direction:")
for row in leaderboard("era", stat_type="pitching", year=2025, n=3, min_ip=50):
    print(f"  {row['name']:22s} {row['value']:.3f}")
"""),
    code("""
for stat, kind in [("era", "pitching"), ("so", "pitching"), ("so", "batting"),
                   ("hr", "batting"), ("whip", "pitching"), ("cwrc+", "batting")]:
    print(f"  {stat:6s} ({kind:8s}) -> {stat_direction(stat, kind)} is better")
"""),
    code("""
# Filter by conference, and carry extra columns through
for row in leaderboard("cwrc+", year=2025, conference="SEC", n=8,
                       include=["hr", "ops"]):
    print(f"  {row['name']:22s} {row['team']:6s} "
          f"cwRC+ {row['value']:6.1f}  {row['hr']:.0f} HR  OPS {row['ops']:.3f}")
"""),
    code("""
# Team names accept any spelling
print("by name   :", [r["name"] for r in leaderboard("hr", year=2025, team="Auburn", n=3)])
print("by acronym:", [r["name"] for r in leaderboard("hr", year=2025, team="AUB", n=3)])
"""),
    code("""
# Career leaderboards aggregate first, rebuilding rates from summed components
print("Career home runs, 2021-2025:")
for row in leaderboard("hr", per="career", n=5, qualifier="noMin"):
    print(f"  {row['name']:22s} {row['value']:5.0f} HR over {row['seasons']} seasons")

print("\\nCareer ERA (minimum 150 innings):")
for row in leaderboard("era", stat_type="pitching", per="career",
                       n=5, min_ip=150, qualifier="noMin"):
    print(f"  {row['name']:22s} {row['value']:.3f} over {row['seasons']} seasons")
"""),
]


# ---------------------------------------------------------------------- draft
NOTEBOOKS["03_draft.ipynb"] = [
    md("""
# MLB Draft

Two layers: the Baseball Almanac history (1965-2025, names and schools) and the
MLB Stats API detail (2021-2026, with signing bonuses, slot values, school class
and biography). Plus MLB Pipeline's pre-draft prospect rankings.

Covers: `parse_mlb_draft`, `get_drafted_players_mlb`,
`get_drafted_players_all_years_mlb`, `get_drafted_players_college`,
`get_drafted_players_all_years_college`, `print_draft_picks_mlb`,
`print_draft_picks_college`, `draft_pick`, `draft_class`, `draft_history`,
`slot_value`, `signing_bonus`, `bonus_vs_slot`, `overslot_picks`,
`biggest_bonuses`, `draft_demographics`, `conference_draft_counts`,
`state_pipeline`, `prospect_rank`, `prospect_board`, `prospect_vs_actual`,
`biggest_draft_risers`, `biggest_draft_fallers`
"""),
    code("""
from ncaa_bbStats import *
"""),
    md("## Draft history, 1965-2025"),
    code("""
# Everyone a club drafted in one year
picks = get_drafted_players_mlb("Boston Red Sox", 2025)
print(f"{len(picks)} picks")
print_draft_picks_mlb(picks[:5])
"""),
    code("""
# Everyone drafted out of one school
picks = get_drafted_players_college("Northeastern", 2025)
print(f"{len(picks)} picks out of Northeastern in 2025")
print_draft_picks_college(picks)
"""),
    code("""
all_picks = get_drafted_players_all_years_college("Northeastern")
print(f"{len(all_picks)} Northeastern players drafted, 1965-2025")

club = get_drafted_players_all_years_mlb("Boston Red Sox")
print(f"{len(club)} players drafted by the Red Sox, all years")
"""),
    code("""
# parse_mlb_draft scrapes Baseball Almanac live; the cache above is built from it.
# Needs the [scrape] extra and a network connection.
try:
    rows = parse_mlb_draft(2025)
    print(f"scraped {len(rows)} picks; first: {rows[0]}")
except Exception as exc:
    print(f"live scrape skipped ({type(exc).__name__}: {exc})")
    print("The cached data used above needs no network.")
"""),
    md("""
## Draft detail, 2021-2026

Signing bonuses, published slot values, school class, and biography.
"""),
    code("""
import json
print(json.dumps(draft_pick(2024, 1), indent=2))
"""),
    code("""
# MLB publishes slot values for the first ten rounds only. Later picks return
# None rather than 0 -- the API literally reports the string "0" there.
print("slot for 2025 pick   1:", f"${slot_value(2025, 1):,}")
print("slot for 2025 pick 100:", f"${slot_value(2025, 100):,}")
print("slot for 2025 pick 400:", slot_value(2025, 400), "(past round 10)")
"""),
    code("""
name = "Kade Anderson"
print(f"{name} signed for ${signing_bonus(name, 2025):,}")
print(f"  which is {bonus_vs_slot(name, 2025):.1%} of slot")
"""),
    code("""
for pick in draft_class("LSU", 2025):
    bonus = f"${pick['signing_bonus']:,}" if pick["signing_bonus"] else "unsigned"
    print(f"  #{pick['pick']:>3}  round {pick['round']:>4}  "
          f"{pick['name']:24s} {pick['position']:4s} {bonus}")
"""),
    code("""
history = draft_history("Vanderbilt", 2021, 2026)
print(f"{len(history)} Vanderbilt players drafted 2021-2026")
first_rounders = [p for p in history if p["round"] == "1"]
print(f"  {len(first_rounders)} first-rounders:",
      [p["name"] for p in first_rounders])
"""),
    code("""
print("Biggest 2025 bonuses:")
for pick in biggest_bonuses(2025, n=5):
    print(f"  ${pick['signing_bonus']:>10,}  #{pick['pick']:<4} "
          f"{pick['name']:24s} {pick['school']}")
"""),
    code("""
print("Signed furthest over slot in 2025:")
for pick in overslot_picks(2025, min_ratio=1.5, n=5):
    print(f"  {pick['bonus_slot_ratio']:.2f}x  #{pick['pick']:<4} "
          f"{pick['name']:24s} ${pick['signing_bonus']:,}")
"""),
    code("""
demographics = draft_demographics(2025)
print(f"2025 draft: {demographics['picks']} picks")
print(f"  by origin       : {demographics['by_origin']}")
print(f"  mean age        : {demographics['mean_age']}")
print(f"  signed          : {demographics['signed']}")
print(f"  total bonuses   : ${demographics['total_bonus_dollars']:,}")
print(f"  top positions   : {dict(list(demographics['by_position'].items())[:5])}")
print(f"  top states      : {dict(list(demographics['top_states'].items())[:5])}")
"""),
    code("""
print("Draft picks produced per conference, 2025:")
for row in conference_draft_counts(2025)[:8]:
    print(f"  {row['conference']:16s} {row['picks']:3d} picks   "
          f"${row['bonus_dollars']:>12,}")
"""),
    code("""
print("Players drafted out of Texas schools:")
for row in state_pipeline("TX"):
    top = row["top_pick"]
    print(f"  {row['season']}  {row['picks']:3d} picks  "
          f"${row['bonus_dollars']:>11,}  best: #{top['pick']} {top['name']}")
"""),
    md("""
## Prospect rankings

MLB Pipeline's pre-draft top 250, useful as a benchmark against where players
actually went.
"""),
    code("""
print("Kade Anderson pre-draft rank:", prospect_rank("Kade Anderson", 2025))

print("\\n2025 board, top 8:")
for row in prospect_board(2025, n=8):
    origin = "college" if row["is_college"] else "high school"
    print(f"  {row['rank']:>3}. {row['name']:24s} {row['position']:6s} "
          f"{row['school']:24s} ({origin})")
"""),
    code("""
# Filter the board
print("Top college left-handers, 2025:")
for row in prospect_board(2025, position="LHP", college_only=True, n=5):
    print(f"  {row['rank']:>3}. {row['name']:24s} {row['school']}")
"""),
    code("""
comparison = prospect_vs_actual(2025)
print(f"{len(comparison)} players on both the board and the draft record\\n")

import statistics
print("rank vs actual pick correlation:",
      round(statistics.correlation([r["prospect_rank"] for r in comparison],
                                   [r["actual_pick"] for r in comparison]), 3))
"""),
    code("""
print("Went much earlier than ranked:")
for row in biggest_draft_risers(2025, n=5):
    print(f"  {row['name']:24s} ranked {row['prospect_rank']:>3} "
          f"-> picked {row['actual_pick']:>3}  ({row['surprise']:+d})")

print("\\nSlid furthest:")
for row in biggest_draft_fallers(2025, n=5):
    print(f"  {row['name']:24s} ranked {row['prospect_rank']:>3} "
          f"-> picked {row['actual_pick']:>3}  ({row['surprise']:+d})")
"""),
]


# ------------------------------------------------------- rpi + program finance
NOTEBOOKS["04_rpi_and_program_finance.ipynb"] = [
    md("""
# RPI, Schedule Strength, and Program Finances

Two team-context datasets, both Division I and both keyed to the registry.

**RPI is Warren Nolan's computation** from public game results, not an official
NCAA statistic. Coverage is 2021-2026; earlier years are not published, so
functions return `None` rather than raising.

**Program finances** come from the federal EADA survey — public-domain data
every Title IV institution must file.

Covers: `rpi`, `rpi_rank`, `rpi_record`, `rpi_table`, `strength_of_schedule`,
`quadrant_record`, `home_road_neutral`, `nonconference_profile`,
`rpi_over_years`, `best_wins`, `program_finance`, `budget_percentile`,
`roster_size`, `coaching_staff_size`, `richest_programs`,
`conference_spending`, `finance_vs_rpi`
"""),
    code("""
from ncaa_bbStats import *
"""),
    md("## RPI and schedule strength"),
    code("""
# Stored as ranks, where 1 is best
print("Tennessee 2024 RPI rank:", rpi_rank("Tennessee", 2024))
print("  strength of schedule :", strength_of_schedule("Tennessee", 2024))

# `rpi` is an alias for `rpi_rank`
print("  via the alias        :", rpi("Tennessee", 2024))

# Outside 2021-2026 there is simply no data
print("\\n2010 (not published):", rpi_rank("Tennessee", 2010))
"""),
    code("""
import json
record = rpi_record("Tennessee", 2024)
print(json.dumps({k: record[k] for k in list(record)[:14]}, indent=2))
"""),
    code("""
# Quadrants group opponents by strength; Q1 is the toughest
for quadrant in (1, 2, 3, 4):
    result = quadrant_record("Tennessee", 2024, quadrant)
    print(f"  Q{quadrant}: {result['wins']:>2}-{result['losses']:<2} "
          f"({result['win_pct']:.3f})")
"""),
    code("""
splits = home_road_neutral("Tennessee", 2024)
for venue, result in splits.items():
    print(f"  {venue:8s} {result['wins']:>2}-{result['losses']:<2} "
          f"({result['win_pct']:.3f})")

print("\\nnon-conference:", nonconference_profile("Tennessee", 2024))
"""),
    code("""
print("Top of the 2025 RPI standings:")
for row in rpi_table(2025, n=10):
    print(f"  {row['rpi_rank']:>3}. {row['team_name']:22s} {row['conference']:12s} "
          f"{row['overall_wins']:>2}-{row['overall_losses']:<2}")
"""),
    code("""
print("SEC by RPI, 2025:")
for row in rpi_table(2025, conference="SEC"):
    print(f"  {row['rpi_rank']:>3}. {row['team_name']:22s} "
          f"{row['overall_wins']:>2}-{row['overall_losses']:<2}")
"""),
    code("""
print("Most Quadrant 1 wins in 2025 -- the best wins against good teams:")
for row in best_wins(2025, n=8):
    print(f"  {row['team_name']:22s} {row['conference']:12s} "
          f"Q1 {row['q1_wins']:>2}-{row['q1_losses']:<2}  RPI {row['rpi_rank']}")
"""),
    code("""
print("Coastal Carolina, season by season:")
for row in rpi_over_years("Coastal Carolina"):
    print(f"  {row['season']}  RPI {row['rpi_rank']:>3}  SOS {row['sos_rank']:>3}  "
          f"{row['wins']:>2}-{row['losses']:<2}  {row['conference']}")
"""),
    md("""
## Program finances

Budget figures are **percentiles within a reporting year**, not dollars.
Baseball budgets inflate a few percent annually, so raw figures are not
comparable across seasons; a percentile is.
"""),
    code("""
import json
print(json.dumps(program_finance("Tennessee", 2025), indent=2))
"""),
    code("""
print("Tennessee 2025 budget percentile:", budget_percentile("Tennessee", 2025))
print("  roster size    :", roster_size("Tennessee", 2025))
print("  coaching staff :", coaching_staff_size("Tennessee", 2025))
"""),
    md("""
### The 2026 caveat

Institutions file the 2025-26 survey in October 2026, so **2026 carries 2025
forward**. Every such row says so, because a carried-forward figure quietly
treated as current is how wrong conclusions get published.
"""),
    code("""
for season in (2025, 2026):
    row = program_finance("Tennessee", season)
    print(f"  season {season}: eada_year={row['eada_year']}, "
          f"carried_forward={row['carried_forward']}")
"""),
    code("""
print("Highest-spending Division I baseball programs, 2025:")
for row in richest_programs(2025, n=10, division=1):
    print(f"  {row['budget_pct']:.3f}  {row['institution_name'][:44]:44s} "
          f"roster {row['roster_size']:.0f}")
"""),
    code("""
print("Median baseball budget percentile by conference, 2025:")
for row in conference_spending(2025)[:10]:
    print(f"  {row['conference']:16s} {row['median_budget_pct']:.4f}  "
          f"({row['programs']} programs)")
"""),
    code("""
# Spending set against results, ready for correlation work
rows = finance_vs_rpi(2025)
print(f"{len(rows)} programs with both a budget percentile and an RPI rank\\n")

import statistics
print("budget percentile vs RPI rank correlation:",
      round(statistics.correlation([r["budget_pct"] for r in rows],
                                   [r["rpi_rank"] for r in rows]), 3),
      "\\n(negative is expected: a better rank is a smaller number)")

print("\\nTop 10 by RPI:")
for row in rows[:10]:
    print(f"  RPI {row['rpi_rank']:>3}  budget {row['budget_pct']:.3f}  "
          f"{row['institution_name'][:40]}")
"""),
]


# -------------------------------------------------------------- cross-dataset
NOTEBOOKS["05_cross_dataset.ipynb"] = [
    md("""
# Cross-Dataset Questions

Questions that need several datasets at once. Each of these is a hand-written
join, and each reports which datasets it could reach — so a missing section
reads as missing rather than as zero.

All of it depends on the team registry to reconcile how differently these
sources spell school names.

Covers: `team_profile`, `player_profile`, `draft_yield`,
`dollars_per_draft_pick`, `conference_report`, `pipeline`, `compare_teams`
"""),
    code("""
from ncaa_bbStats import *
"""),
    md("## One program, one season, every dataset"),
    code("""
profile = team_profile("Tennessee", 2024)

identity = profile["identity"]
print(f"{identity['canonical_name']}  ({identity['conference']}, "
      f"Division {identity['division']})")
print(f"  IPEDS {identity['ipeds_unitid']} -- {identity['institution_name']}")

record = profile["record"]
print(f"\\n  record    {record['wins']}-{record['losses']}  ({record['win_pct']})")
print(f"  RPI       {profile['rpi']['rpi_rank']}  "
      f"(SOS {profile['rpi']['sos_rank']})")
print(f"  Q1        {profile['rpi']['q1_wins']}-{profile['rpi']['q1_losses']}")
print(f"  budget    {profile['finance']['budget_pct']:.3f} percentile")
print(f"  roster    {profile['finance']['roster_size']:.0f}")
print(f"  drafted   {profile['draft']['picks']} players")
print(f"  pythag    expected {profile['pythagorean']['expected_win_pct']}, "
      f"actual {profile['pythagorean']['actual_win_pct']}")
"""),
    code("""
# Which datasets were reachable
print(profile["coverage"])

print("\\nThe draft class:")
for pick in profile["draft"]["selections"]:
    bonus = f"${pick['signing_bonus']:,}" if pick["signing_bonus"] else "-"
    print(f"  #{pick['pick']:>3}  {pick['name']:24s} {pick['position']:4s} {bonus}")
"""),
    code("""
# A Division III program has no RPI or draft data -- and says so
profile = team_profile("Amherst", 2015)
if profile:
    print(profile["identity"]["canonical_name"], profile["identity"]["division"])
    print("coverage:", profile["coverage"])
    print("rpi is None:", profile["rpi"] is None)
"""),
    md("## One player, every dataset"),
    code("""
player = player_profile("Kade Anderson")
print(f"{player['name']}  ({player['role']})")
print(f"  seasons played : {player['seasons_played']}")
print(f"  program        : {player['team']['canonical_name']} "
      f"({player['team']['conference']})")

pitching = player["pitching"]
print(f"\\n  {player['season']}: {pitching['so']:.0f} K in {pitching['ip']} IP, "
      f"ERA {pitching['era']:.2f}, cFIP {pitching['cfip']:.2f}")

draft = player["draft"]
print(f"\\n  drafted #{draft['pick']} by the {draft['team_name']}")
print(f"  bonus ${draft['signing_bonus']:,} against a ${draft['slot_value']:,} slot")
print(f"  pre-draft rank: {player['prospect_rank']}")
print(f"\\n  coverage: {player['coverage']}")
"""),
    md("## Programs as talent pipelines"),
    code("""
for team in ["LSU", "Vanderbilt", "Tennessee", "Northeastern"]:
    result = draft_yield(team, 2021, 2026)
    print(f"  {result['team']:16s} {result['picks']:3d} picks "
          f"({result['picks_per_year']:.1f}/yr)  "
          f"{result['first_round_picks']} first-rounders  "
          f"${result['total_bonus_dollars']:>12,}")
"""),
    code("""
result = draft_yield("LSU", 2021, 2026)
print("LSU, year by year:")
for season, row in sorted(result["by_year"].items()):
    print(f"  {season}  {row['picks']:2d} picks  ${row['bonus_dollars']:>11,}")
print(f"\\n  best pick: #{result['best_pick']['pick']} "
      f"{result['best_pick']['name']} ({result['best_pick']['year']})")
"""),
    md("""
### Budget in, prospects out

Budget is a percentile rather than dollars, so this is not a literal cost per
pick — it pairs spending rank with draft output, which is the comparison that
travels across seasons.
"""),
    code("""
for team in ["Tennessee", "LSU", "Vanderbilt", "Coastal Carolina",
             "Northeastern", "Utah Tech"]:
    row = dollars_per_draft_pick(team, 2021, 2025)
    budget = f"{row['mean_budget_pct']:.3f}" if row["mean_budget_pct"] else "  n/a"
    print(f"  {row['team']:18s} budget {budget}  ->  "
          f"{row['picks_per_year']:.1f} picks/yr  "
          f"(${row['bonus_dollars_per_year']:>11,.0f}/yr)")
"""),
    md("## Conferences"),
    code("""
report = conference_report("SEC", 2025)
print(f"{report['conference']} {report['season']}")
print(f"  programs      : {report['programs']}")
print(f"  draft picks   : {report['draft_picks']}")
print(f"  bonus dollars : ${report['bonus_dollars']:,}")
print(f"  median budget : {report['median_budget_pct']}")
print(f"  best RPI      : {report['best_rpi_rank']}")
print(f"\\n  standings:")
for row in report["standings"][:8]:
    print(f"    RPI {row['rpi_rank']:>3}  {row['team']:22s} "
          f"{row['wins']:>2}-{row['losses']:<2}")
"""),
    md("## A program's trajectory"),
    code("""
print("Coastal Carolina, 2021-2026:")
print(f"  {'yr':4s} {'conf':10s} {'W-L':>7s} {'RPI':>5s} {'budget':>8s} {'picks':>6s}")
for row in pipeline("Coastal Carolina"):
    print(f"  {row['season']} {row['conference']:10s} "
          f"{str(row['wins']) + '-' + str(row['losses']):>7s} "
          f"{str(row['rpi_rank']):>5s} "
          f"{row['budget_pct']:>8.3f} {row['draft_picks']:>6d}")
"""),
    md("## Side by side"),
    code("""
rows = compare_teams(["Tennessee", "LSU", "Coastal Carolina",
                      "Northeastern", "Utah Tech"], 2025)
print(f"  {'team':18s} {'conf':10s} {'W-L':>7s} {'RPI':>5s} {'budget':>8s} {'picks':>6s}")
for row in rows:
    print(f"  {row['team']:18s} {str(row['conference']):10s} "
          f"{str(row['wins']) + '-' + str(row['losses']):>7s} "
          f"{str(row['rpi_rank']):>5s} "
          f"{row['budget_pct']:>8.3f} {row['draft_picks']:>6d}")
"""),
    md("""
## Recipe: draft picks per dollar spent

The kind of question that needs three datasets and the registry to connect them.
"""),
    code("""
picks = {row["conference"]: row["picks"] for row in conference_draft_counts(2025)}

print(f"  {'conference':16s} {'budget':>8s} {'picks':>6s}")
for row in conference_spending(2025)[:12]:
    count = picks.get(row["conference"], 0)
    print(f"  {row['conference']:16s} {row['median_budget_pct']:>8.3f} {count:>6d}")
"""),
]


# ------------------------------------------------------------------- scouting
NOTEBOOKS["06_scouting.ipynb"] = [
    md("""
# Scouting and Draft Prediction

Two models: a classifier for whether a player-season leads to being drafted, and
a regressor for where a drafted player falls within their college class.

Both are trained only on public NCAA statistics and this package's own derived
metrics. **Read `model_card()` before quoting any of these numbers** — it
carries the limitations.

Needs the `model` extra (`pip install "ncaa_bbStats[model]"`); explanations use
`explain` for SHAP, falling back to gain-based attribution otherwise.

Covers: `scouting_report`, `predict_draft_probability`, `predict_draft_order`,
`draft_board`, `explain_prediction`, `feature_contributions`,
`predict_from_stats`, `is_draft_eligible`, `model_card`
"""),
    code("""
from ncaa_bbStats import *
"""),
    md("## A scouting report"),
    code("""
print(scouting_report("Kade Anderson", 2025))
"""),
    md("## The individual predictions behind it"),
    code("""
for name in ["Kade Anderson", "Jamie Arnold", "Gavin Kilen", "Jac Caglianone"]:
    probability = predict_draft_probability(name, 2025)
    if probability is None:
        print(f"  {name:22s} not in the eligible population")
        continue
    order = predict_draft_order(name, 2025)
    print(f"  {name:22s} P(drafted) {probability:.1%}   "
          f"projected college order ~{order:.0f}")
"""),
    md("""
### Eligibility is inferred, not looked up

It comes from seasons completed and from age — and age is itself estimated for
most players. So the basis is returned alongside the answer.
"""),
    code("""
for name in ["Kade Anderson", "Jamie Arnold", "Jac Caglianone"]:
    result = is_draft_eligible(name, 2025)
    if result is None:
        # Caglianone was drafted in 2024, so he has no 2025 college season.
        print(f"  {name:22s} no 2025 season in the data")
        continue
    eligible, basis = result
    print(f"  {name:22s} eligible={eligible}  basis={basis!r}")
"""),
    md("""
## What drove the prediction

SHAP where installed, gain-weighted deviation from the median otherwise. Impact
is in percentage points of draft probability.
"""),
    code("""
explanation = explain_prediction("Kade Anderson", 2025, top_n=6)
print(f"method: {explanation['method']}")
print(f"draft probability: {explanation['draft_probability']:.1%}\\n")

print("strengths:")
for row in explanation["strengths"]:
    print(f"  ^ {row['label']:28s} {row['value']:>10.3f} "
          f"(median {row['median']:>8.3f})  {row['impact']:+.2f}%")

print("\\nconcerns:")
for row in explanation["concerns"]:
    print(f"  v {row['label']:28s} {row['value']:>10.3f} "
          f"(median {row['median']:>8.3f})  {row['impact']:+.2f}%")
"""),
    code("""
# The gain fallback works with no SHAP installed
fallback = explain_prediction("Kade Anderson", 2025, method="gain", top_n=3)
print("method:", fallback["method"])
for row in fallback["strengths"]:
    print(f"  ^ {row['label']:28s} {row['impact']:+.2f}")
"""),
    md("""
### Contributions that add up

`explain_prediction` returns a readable shortlist, and its impacts are
leave-one-out figures that deliberately do not sum to anything. When you need an
attribution that *does* — to stack into a waterfall, say — use
`feature_contributions`, which returns the base value and every feature's raw
contribution in the model's own units, guaranteeing
`base + sum(contributions) == prediction`.

Stage 1 works in log-odds, so apply a logistic to read a probability. Stage 2 is
already in college draft order units. Requires the `explain` extra; there is no
gain fallback, because gain has no base value.
"""),
    code("""
from math import exp

stage1 = feature_contributions("Kade Anderson", 2025, stage=1)
total = stage1["base"] + sum(c["contribution"] for c in stage1["contributions"])
print(f"units: {stage1['units']}   features: {len(stage1['contributions'])}")
print(f"base {stage1['base']:+.3f} -> prediction {stage1['prediction']:+.3f} "
      f"(sum checks: {abs(total - stage1['prediction']) < 1e-9})")
print(f"as a probability: {1 / (1 + exp(-stage1['base'])):.1%} -> "
      f"{1 / (1 + exp(-stage1['prediction'])):.1%}\\n")

for row in stage1["contributions"][:6]:
    value = "not supplied" if row["value"] is None else f"{row['value']:.3f}"
    print(f"  {row['label']:28s} {value:>12s}  {row['contribution']:+.3f}")

stage2 = feature_contributions("Kade Anderson", 2025, stage=2)
print(f"\\nstage 2 ({stage2['units']}): {stage2['base']:.1f} -> "
      f"{stage2['prediction']:.1f}")
"""),
    code("""
# The same function explains a stat line that was never in the data: hand it the
# feature_row that predict_from_stats scored, so the explanation and the number
# come from one row rather than two.
scored = predict_from_stats(
    "pitcher", 21,
    {"era_pitch": 2.40, "so_pitch": 130, "bb_pitch": 25, "ip_pitch": 95.0},
    team="LSU", season=2025,
)
custom = feature_contributions(features=scored["feature_row"], stage=1)
print(f"P(drafted) {scored['draft_probability']:.1%}, "
      f"from {len(scored['supplied_features'])} supplied statistics")
for row in custom["contributions"][:5]:
    value = "not supplied" if row["value"] is None else f"{row['value']:.3f}"
    print(f"  {row['label']:28s} {value:>12s}  {row['contribution']:+.3f}")
"""),
    md("""
## A whole season, ranked

`draft_board` scores every eligible player. Comparing against `actual_pick`
shows where the model agreed with the draft and where it did not.
"""),
    code("""
board = draft_board(2026, n=15)   # 2026 is the model's held-out season
print(f"  {'#':>3} {'player':24s} {'team':6s} {'P(draft)':>9s} {'grade':>6s} "
      f"{'proj':>6s} {'actual':>7s}")
for row in board:
    projected = f"{row['predicted_order']:.0f}" if row["predicted_order"] else "-"
    actual = f"#{row['actual_pick']}" if row["actual_pick"] else "undrafted"
    print(f"  {row['rank']:>3} {row['name']:24s} {row['team']:6s} "
          f"{row['draft_probability']:>9.3f} {row['draft_grade']:>6s} "
          f"{projected:>6s} {actual:>7s}")
"""),
    code("""
# How much of the top of the board was actually drafted?
top50 = draft_board(2026, n=50)
hit = sum(1 for row in top50 if row["actual_pick"])
print(f"{hit} of the top 50 were drafted ({hit / 50:.0%})")

# Draft position is suppressed below 25%: the order model is trained only on
# drafted players, so applying it lower down would be extrapolation.
low = [r for r in draft_board(2026, n=2000) if r["draft_probability"] < 0.25]
print(f"\\n{len(low)} players below the 25% threshold; "
      f"all have predicted_order suppressed: "
      f"{all(r['predicted_order'] is None for r in low)}")
"""),
    md("""
## Scoring a line that is not in the data

Supply as much or as little as you have. Unspecified statistics stay missing,
which the models handle natively, and the result reports how much was imputed.
"""),
    code("""
result = predict_from_stats(
    "pitcher", age=21,
    stats={"era": 2.40, "so": 130, "bb": 25, "ip": 95.0,
           "h": 68, "hr": 5, "g": 16, "gs": 16, "tbf": 370},
    team="LSU", name="Prospect A",   # season defaults to the most recent
)
print(result["report"])
"""),
    code("""
print("supplied:", result["supplied_features"])
print("confidence:", result["confidence"])
print("draft probability:", round(result["draft_probability"], 4))
print("predicted order:", result["predicted_order"])
"""),
    code("""
# A weaker line, with no team given -- context falls back to the season median
weak = predict_from_stats(
    "batter", age=19,
    stats={"avg": 0.240, "hr": 1, "pa": 90, "ab": 80},
    name="Prospect B",   # no team either: context falls back to the league median
)
print(weak["report"])
"""),
    code("""
# The model responds to the input: same role and age, different production
strong = predict_from_stats("pitcher", 21,
    {"era": 1.80, "so": 150, "bb": 15, "ip": 100.0, "h": 60, "hr": 3,
     "g": 16, "gs": 16}, team="LSU")
poor = predict_from_stats("pitcher", 21,
    {"era": 7.50, "so": 12, "bb": 20, "ip": 18.0, "h": 30, "hr": 6,
     "g": 9, "gs": 1}, team="LSU")

print(f"  strong line: {strong['draft_probability']:.1%}  "
      f"grade {strong['draft_grade']}")
print(f"  poor line  : {poor['draft_probability']:.1%}  "
      f"grade {poor['draft_grade']}")
"""),
    md("""
## The model card

Published as a function rather than a documentation footnote, so the
limitations travel with the predictions.
"""),
    code("""
card = model_card()
print(f"version    : {card['model_version']}")
print(f"trained on : {card['train_years']}")
print(f"tested on  : {card['test_year']}")
print(f"eligibility: {card['eligibility']}")

print(f"\\nstage 1 (drafted or not): {card['stage1']['metrics']}")
print(f"stage 2 (draft order)   : {card['stage2']['metrics']}")
"""),
    code("""
print("Stage 3 is deliberately not shipped:")
print(" ", card["stage3"]["reason"])
"""),
    code("""
print("Limitations:")
for i, limitation in enumerate(card["limitations"], 1):
    print(f"\\n  {i}. {limitation}")
"""),
    code("""
reference = card["reference_implementation"]
print("For comparison only -- NOT this package's numbers:")
print(f"  {reference['note']}\\n")
print(f"  reference PR-AUC   {reference['stage1_pr_auc']}   "
      f"vs this package {card['stage1']['metrics']['pr_auc']}")
print(f"  reference ROC-AUC  {reference['stage1_roc_auc']}   "
      f"vs this package {card['stage1']['metrics']['roc_auc']}")
print(f"  reference Spearman {reference['stage2_spearman']}   "
      f"vs this package {card['stage2']['metrics']['spearman']}")
"""),
]


def build(notebook_dir, execute=True):
    kernel = {
        "kernelspec": {"display_name": "Python 3", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    }
    written = []
    for filename, cells in NOTEBOOKS.items():
        path = os.path.join(notebook_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"cells": cells, "metadata": kernel,
                       "nbformat": 4, "nbformat_minor": 5}, f, indent=1)
            f.write("\n")
        code_cells = sum(1 for c in cells if c["cell_type"] == "code")
        print(f"  wrote {filename}  ({code_cells} code cells)")
        written.append(path)

    if not execute:
        return written

    print("\nexecuting ...")
    for path in written:
        result = subprocess.run(
            [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook",
             "--execute", "--inplace", "--ExecutePreprocessor.timeout=600", path],
            capture_output=True, text=True,
        )
        status = "ok" if result.returncode == 0 else "FAILED"
        print(f"  {status:6s} {os.path.basename(path)}")
        if result.returncode != 0:
            print(result.stderr[-3000:])
            raise SystemExit(1)
    return written


def check_environment():
    """Refuse to run against a copy of the package other than this repo.

    A stale non-editable install in site-packages shadows the working tree, and
    the notebooks then execute against whatever data that copy carries -- which
    looks like a successful run and silently bakes the wrong outputs in. Caught
    exactly that: an old 1.2.0 install produced notebooks showing a model
    trained on 2021-2024.
    """
    import ncaa_bbStats

    imported = os.path.realpath(os.path.dirname(ncaa_bbStats.__file__))
    expected = os.path.realpath(os.path.join(HERE, "..", "src", "ncaa_bbStats"))
    if imported != expected:
        raise SystemExit(
            f"ncaa_bbStats resolves to\n    {imported}\n"
            f"but this repo is at\n    {expected}\n\n"
            "Reinstall it as editable so the notebooks run against the working "
            "tree:\n    pip install -e .\n"
        )
    print(f"importing ncaa_bbStats from {imported}")


def check_coverage():
    """Every public name must appear in some notebook."""
    import ncaa_bbStats

    text = " ".join(
        "".join(cell["source"]) for cells in NOTEBOOKS.values() for cell in cells
    )
    missing = sorted(n for n in ncaa_bbStats.__all__ if n not in text)
    if missing:
        print(f"\n!! {len(missing)} public functions not demonstrated: {missing}")
        return False
    print(f"\nall {len(ncaa_bbStats.__all__)} public functions are demonstrated")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-exec", action="store_true",
                        help="Write the notebooks without running them.")
    args = parser.parse_args(argv)

    check_environment()
    covered = check_coverage()
    build(HERE, execute=not args.no_exec)
    return 0 if covered else 1


if __name__ == "__main__":
    raise SystemExit(main())
