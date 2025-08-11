import json
import os
from team_stats import *

# Define the years and divisions that is going to be scraped
years = [2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
         2020, 2021, 2022, 2023, 2024, 2025]
divisions = [1, 2, 3]

# Base folder for cache files
base_cache_dir = "../data/team_stats_cache"

for year in years:
    for division in divisions:
        print(f"Scraping data for year: {year}, division: {division}...")

        try:
            bb = base_on_balls(year=year, division=division)
            ba = batting_average(year=year, division=division)
            dp = double_plays(year=year, division=division)
            dppg = double_plays_per_game(year=year, division=division)
            d = doubles(year=year, division=division)
            dpg = doubles_per_game(year=year, division=division)
            era = earned_run_average(year=year, division=division)
            fpct = fielding_percentage(year=year, division=division)
            hb = hit_batters(year=year, division=division)
            hbp = hit_by_pitch(year=year, division=division)
            h = hits(year=year, division=division)
            hapni = hits_allowed_per_nine_innings(year=year, division=division)
            hr = home_runs(year=year, division=division)
            hrpg = home_runs_per_game(year=year, division=division)
            obp = on_base_percentage(year=year, division=division)
            r = runs(year=year, division=division)
            sb = sacrifice_bunts(year=year, division=division)
            sf = sacrifice_flies(year=year, division=division)
            s = scoring(year=year, division=division)
            so = shutouts(year=year, division=division)
            spct = slugging_percentage(year=year, division=division)
            sb = stolen_bases(year=year, division=division)
            sbpg = stolen_bases_per_game(year=year, division=division)
            sowr = strikeout_to_walk_ratio(year=year, division=division)
            sopni = strikeouts_per_nine_innings(year=year, division=division)
            tp = triple_plays(year=year, division=division)
            t = triples(year=year, division=division)
            tpg = triples_per_game(year=year, division=division)
            whip_stat = whip(year=year, division=division)
            wpct = winning_percentage(year=year, division=division)
            wapni = walks_allowed_per_nine_innings(year=year, division=division)

            stat_dicts = [
                wpct, bb, ba, dp, dppg, d, dpg, era, fpct, hb, hbp, h,
                hapni, hr, hrpg, obp, r, sb, sf, s, so, spct, sb, sbpg,
                sowr, sopni, tp, t, tpg, whip_stat, wapni
            ]
            filtered_stats = [d for d in stat_dicts if d is not None]

            combined_stats = combine_team_stats(*filtered_stats)
            combined_stats["division"] = int(division)

            output_dir = os.path.join(base_cache_dir, f"div{division}")
            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(output_dir, f"{year}.json")
            with open(output_path, "w") as f:
                json.dump(combined_stats, f)

        except Exception as e:
            print(f"Skipping year {year}, division {division} due to error: {e}")


print("Scraping and caching complete!")
