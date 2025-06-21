import psycopg2
from config import DB_CONFIG
from player_stats import fetch_player_stats


def create_player_tables():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Add this at the top of create_player_tables()
    cur.execute("DROP TABLE IF EXISTS batters")
    cur.execute("DROP TABLE IF EXISTS pitchers")

    # Create batters table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS batters (
            id SERIAL PRIMARY KEY,
            player_name TEXT,
            team TEXT,
            class TEXT,
            pos TEXT,
            gp INT,
            pa INT,
            ab INT,
            r INT,
            h INT,
            "2B" INT,
            "3B" INT,
            hr INT,
            rbi INT,
            hbp INT,
            bb INT,
            so INT,
            sb INT,
            cs INT,
            avg FLOAT,
            obp FLOAT,
            slg FLOAT,
            ops FLOAT,
            season INT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create pitchers table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pitchers (
            id SERIAL PRIMARY KEY,
            player_name TEXT,
            team TEXT,
            class TEXT,
            w INT,
            l INT,
            era FLOAT,
            app INT,
            gs INT,
            cg INT,
            sho INT,
            sv INT,
            ip FLOAT,
            h INT,
            r INT,
            er INT,
            bb INT,
            so INT,
            hbp INT,
            baa FLOAT,
            season INT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    cur.close()
    conn.close()


def insert_players(players, stat_type):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for player in players:
        p = lambda k: player.get(k, None)

        if stat_type == 'batting':
            cur.execute('''
                INSERT INTO batters (
                    player_name, team, class, pos, gp, pa, ab, r, h, "2B", "3B", hr, rbi,
                    hbp, bb, so, sb, cs, avg, obp, slg, ops, season
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                p('Player'), p('Team'), p('Class'), p('POS'),
                to_int(p('GP')), to_int(p('PA')), to_int(p('AB')),
                to_int(p('R')), to_int(p('H')), to_int(p('2B')), to_int(p('3B')),
                to_int(p('HR')), to_int(p('RBI')), to_int(p('HBP')),
                to_int(p('BB')), to_int(p('K')), to_int(p('SB')), to_int(p('CS')),
                to_float(p('BA')), to_float(p('OBP')), to_float(p('SLG')), to_float(p('OPS')), to_int(p('Season'))
            ))

        elif stat_type == 'pitching':
            cur.execute('''
                INSERT INTO pitchers (
                    player_name, team, class, w, l, era, app, gs, cg, sho, sv,
                    ip, h, r, er, bb, so, hbp, baa, season
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                p('Player'), p('Team'), p('Class'),
                to_int(p('W')), to_int(p('L')), to_float(p('ERA')),
                to_int(p('APP')), to_int(p('GS')), to_int(p('CG')), to_int(p('SHO')),
                to_int(p('SV')), to_float(p('IP')), to_int(p('H')), to_int(p('R')), to_int(p('ER')),
                to_int(p('BB')), to_int(p('K')), to_int(p('HBP')), to_float(p('BA')), to_int(p('Season'))
            ))

    conn.commit()
    cur.close()
    conn.close()


def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


if __name__ == '__main__':
    create_player_tables()

    for year in range(2016, 2026):
        url = f'https://d1baseball.com/statistics/?season={year}'
        print(f"📅 Processing season {year}...")

        batters = fetch_player_stats(stat_type='batting', url=url)
        insert_players(batters, stat_type='batting')

        pitchers = fetch_player_stats(stat_type='pitching', url=url)
        insert_players(pitchers, stat_type='pitching')

    print("✅ Finished inserting players for all seasons.")
