import psycopg2
from config import DB_CONFIG
from stats import *

bb = base_on_balls()
ba = batting_average()
dp = double_plays()
dppg = double_plays_per_game()
d = doubles()
dpg = doubles_per_game()
era = earned_run_average()
fpct = fielding_percentage()
hb = hit_batters()
hbp = hit_by_pitch()
h = hits()
hapni = hits_allowed_per_nine_innings()
hr = home_runs()
hrpg = home_runs_per_game()
obp = on_base_percentage()
r = runs()
sb = sacrifice_bunts()
sf = sacrifice_flies()
s = scoring()
so = shutouts()
spct = slugging_percentage()
sb = stolen_bases()
sbpg = stolen_bases_per_game()
sowr = strikeout_to_walk_ratio()
sopni = strikeouts_per_nine_innings()
tp = triple_plays()
t = triples()
tpg = triples_per_game()
whip = whip()
wpct = winning_percentage()
wapni = walks_allowed_per_nine_innings()

combined_stats = combine_team_stats(wpct, bb, ba, dp, dppg, d, dpg, era, fpct, hb, hbp, h, hapni, hr, hrpg, obp, r,
                                        sb, sf, s, so, spct, sb, sbpg, sowr, sopni, tp, t, tpg, whip, wapni)


# 1. Database Setup Script
def create_stats_database():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    # Create table with properly quoted column names
    cur.execute('''
                CREATE TABLE IF NOT EXISTS team_stats
                (
                    team
                    VARCHAR
                (
                    255
                ) NOT NULL,
                    league VARCHAR
                (
                    50
                ) NOT NULL,
                    "W" INT,
                    "L" INT,
                    "T" INT,
                    "WPCT" FLOAT,
                    "G" INT,
                    "BB (Batting)" INT,
                    "AB" INT,
                    "H" INT,
                    "BA" FLOAT,
                    "DP" INT,
                    "DPPG" FLOAT,
                    "2B" INT,
                    "2BPG" FLOAT,
                    "IP" FLOAT,
                    "R (Pitching)" INT,
                    "ER" INT,
                    "ERA" FLOAT,
                    "PO" INT,
                    "A" INT,
                    "E" INT,
                    "FPCT" FLOAT,
                    "HB" INT,
                    "HBP" INT,
                    "HA" INT,
                    "HAPG" FLOAT,
                    "HR" INT,
                    "HRPG" FLOAT,
                    "SF" INT,
                    "SH" INT,
                    "OBP" FLOAT,
                    "R (Batting)" INT,
                    "SB" INT,
                    "CS" INT,
                    "RPG" FLOAT,
                    "SHO" INT,
                    "TB" INT,
                    "SLG" FLOAT,
                    "SBPG" FLOAT,
                    "SO" INT,
                    "BB (Pitching)" INT,
                    "K/BB" FLOAT,
                    "K/9" FLOAT,
                    "3B" INT,
                    "3BPG" FLOAT,
                    "WHIP" FLOAT,
                    "BBPG (Pitching)" FLOAT,
                    "TP" INT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY
                (
                    team,
                    league
                )
                    )
                ''')

    # Upsert data with proper quoting
    for (team, league), stats in combined_stats.items():
        # Remove team/league from stats if present
        stats_clean = {k: v for k, v in stats.items() if k not in ('team', 'league')}

        columns = ['team', 'league'] + [f'"{k}"' for k in stats_clean.keys()]
        values = [team, league] + list(stats_clean.values())

        update_cols = [f'"{k}" = EXCLUDED."{k}"' for k in stats_clean.keys()]

        cur.execute(f'''
            INSERT INTO team_stats ({', '.join(columns)})
            VALUES ({', '.join(['%s'] * len(values))})
            ON CONFLICT (team, league) DO UPDATE SET
                {', '.join(update_cols)}
        ''', values)

    conn.commit()
    cur.close()
    conn.close()


# 2. Win Probability Function using DB
def get_win_probability(team1, team2):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get team1 stats
    cur.execute('SELECT * FROM team_stats WHERE team = %s', (team1,))
    team1_stats = cur.fetchone()

    # Get team2 stats
    cur.execute('SELECT * FROM team_stats WHERE team = %s', (team2,))
    team2_stats = cur.fetchone()

    cur.close()
    conn.close()

    if not team1_stats or not team2_stats:
        raise ValueError("One or both teams not found in database")

    # Convert tuples to dicts (adjust indices based on your schema)
    stats_dict = lambda t: {
        'W': t[2], 'L': t[3], 'G': t[4],
        'ERA': t[5], 'OBP': t[6], 'WHIP': t[7],
        'WPCT': t[8], 'league': t[1]
    }

    return calculate_win_probability(
        stats_dict(team1_stats),
        stats_dict(team2_stats),
        combined_stats
    )
