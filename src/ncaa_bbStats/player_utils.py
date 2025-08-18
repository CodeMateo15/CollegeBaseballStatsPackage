import os
from functools import lru_cache
from typing import Literal, Optional, Sequence
import pandas as pd

_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "player_stats_cache")
)

Qualifier = Literal["qualified", "noMin"]
StatType = Literal["batting", "pitching"]


# Paths and loading

def get_player_csv_path(stat_type: StatType, qualifier: Qualifier) -> str:
    """Return absolute path to the player CSV for the given type/qualifier."""
    fname = f"{stat_type}_{qualifier}.csv"
    return os.path.join(_DATA_DIR, stat_type, fname)


@lru_cache(maxsize=8)
def _load_df(stat_type: StatType, qualifier: Qualifier) -> pd.DataFrame:
    """Load the CSV into a DataFrame (cached). Does minimal cleanup."""
    path = get_player_csv_path(stat_type, qualifier)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing player stats file: {path}")
    df = pd.read_csv(path)
    # Normalize column names and strip
    df.columns = [c.strip() for c in df.columns]
    # Normalize string columns
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str).str.strip()
    return df


# Listing utilities (lists for notebooks)

def list_available_years(stat_type: StatType, qualifier: Qualifier) -> list[int]:
    """Sorted unique years available in the CSV."""
    df = _load_df(stat_type, qualifier)
    if "year" not in df.columns:
        return []
    yrs = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int).unique().tolist()
    return sorted(yrs)


def list_players(
    stat_type: StatType,
    qualifier: Qualifier,
    year: Optional[int] = None,
    team_substr: Optional[str] = None,
) -> list[str]:
    """Return a sorted list of player names, optionally filtered by year and team substring."""
    df = _load_df(stat_type, qualifier)
    m = pd.Series(True, index=df.index)
    if year is not None and "year" in df.columns:
        m &= df["year"].astype(str) == str(int(year))
    if team_substr and "team" in df.columns:
        m &= df["team"].str.lower().str.contains(team_substr.lower(), na=False)
    names = df.loc[m, "name"].dropna().astype(str).unique().tolist()
    return sorted(names)


def player_seasons(stat_type: StatType, qualifier: Qualifier, player_name: str) -> list[int]:
    """Return sorted years where a player appears in the dataset."""
    df = _load_df(stat_type, qualifier)
    m = df["name"].str.lower() == player_name.lower()
    if "year" not in df.columns:
        return []
    yrs = pd.to_numeric(df.loc[m, "year"], errors="coerce").dropna().astype(int).unique().tolist()
    return sorted(yrs)


# Core getters (simple float and list outputs)

def get_player_stat(
    stat_type: StatType,
    qualifier: Qualifier,
    player_name: str,
    stat: str,
    year: Optional[int] = None,
    team_substr: Optional[str] = None,
) -> float | None:
    """
    Get a single stat for a player. If multiple rows match (e.g., transfers), returns the sum.
    - stat: column name like "hr", "rbi", "obp", "era" (case-insensitive match).
    - year: if provided, filter to that season.
    - team_substr: optionally narrow to a team substring.

    Returns a float or None if not found or non-numeric.
    """
    df = _load_df(stat_type, qualifier)

    # Resolve column name case-insensitively
    colmap = {c.lower(): c for c in df.columns}
    if stat.lower() not in colmap:
        return None
    scol = colmap[stat.lower()]

    m = df["name"].str.lower() == player_name.lower()
    if year is not None and "year" in df.columns:
        m &= df["year"].astype(str) == str(int(year))
    if team_substr and "team" in df.columns:
        m &= df["team"].str.lower().str.contains(team_substr.lower(), na=False)

    sub = df.loc[m, scol]
    if sub.empty:
        return None

    vals = pd.to_numeric(sub, errors="coerce").dropna()
    if vals.empty:
        return None

    return float(vals.sum())


def get_player_rows(
    stat_type: StatType,
    qualifier: Qualifier,
    player_name: str,
    year: Optional[int] = None,
    team_substr: Optional[str] = None,
    include_columns: Optional[Sequence[str]] = None,
) -> list[dict]:
    """
    Return a list of row dicts for a player (optionally filtered by year/team).
    If include_columns is provided, only those columns are kept (if present).
    """
    df = _load_df(stat_type, qualifier)
    m = df["name"].str.lower() == player_name.lower()
    if year is not None and "year" in df.columns:
        m &= df["year"].astype(str) == str(int(year))
    if team_substr and "team" in df.columns:
        m &= df["team"].str.lower().str.contains(team_substr.lower(), na=False)
    sub = df.loc[m]

    if include_columns:
        keep = [c for c in include_columns if c in sub.columns]
        if keep:
            sub = sub[keep]
    return sub.to_dict(orient="records")


def top_players(
    stat_type: StatType,
    stat: str,
    n: int = 10,
    year: Optional[int] = None,
    team_substr: Optional[str] = None,
) -> list[dict]:
    """
    Return top-N players by a stat as a list of dicts: {name, team, year, value}.
    """
    df = _load_df(stat_type, "qualified")
    colmap = {c.lower(): c for c in df.columns}
    if stat.lower() not in colmap:
        return []
    scol = colmap[stat.lower()]

    work = df.copy()
    m = pd.Series(True, index=work.index)
    if year is not None and "year" in work.columns:
        m &= work["year"].astype(str) == str(int(year))
    if team_substr and "team" in work.columns:
        m &= work["team"].str.lower().str.contains(team_substr.lower(), na=False)

    sub = work.loc[m, ["name", "team", "year", scol]].copy()
    sub[scol] = pd.to_numeric(sub[scol], errors="coerce")
    sub = sub.dropna(subset=[scol])
    sub = sub.sort_values(by=scol, ascending=False).head(n)

    out = []
    for _, r in sub.iterrows():
        out.append({
            "name": r.get("name"),
            "team": r.get("team"),
            "year": int(r.get("year")) if pd.notna(r.get("year")) else None,
            "value": float(r.get(scol)) if pd.notna(r.get(scol)) else None,
        })
    return out


# Helpers

def _ip_to_float(ip_series: pd.Series) -> pd.Series:
    """Convert IP like 123.1 (1/3) and 123.2 (2/3) to floats as a Series."""
    def _one(x: object) -> float | None:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return None
        s = str(x).strip()
        if not s:
            return None
        try:
            if "." in s:
                whole, frac = s.split(".", 1)
                whole_i = int(whole) if whole else 0
                d = frac[:1]
                if d == "1":
                    return whole_i + (1.0/3.0)
                if d == "2":
                    return whole_i + (2.0/3.0)
                return float(s)
            return float(s)
        except Exception:
            return None
    return ip_series.apply(_one).astype(float)


def batting_stat(
    player_name: str,
    stat: str,
    qualifier: Qualifier = "noMin",
    year: Optional[int] = None,
    team_substr: Optional[str] = None,
) -> float | None:
    """Convenience wrapper for batting stats using get_player_stat (sums across matching rows)."""
    return get_player_stat("batting", qualifier, player_name, stat, year=year, team_substr=team_substr)



def pitching_stat(
    player_name: str,
    stat: str,
    qualifier: Qualifier = "noMin",
    year: Optional[int] = None,
    team_substr: Optional[str] = None,
) -> float | None:
    """Convenience wrapper for pitching stats using get_player_stat (sums across matching rows)."""
    return get_player_stat("pitching", qualifier, player_name, stat, year=year, team_substr=team_substr)



def list_batters(qualifier: Qualifier = "noMin", year: Optional[int] = None, team_substr: Optional[str] = None) -> list[str]:
    """List batter names, optionally filtered by year/team."""
    return list_players("batting", qualifier, year=year, team_substr=team_substr)


def list_pitchers(qualifier: Qualifier = "noMin", year: Optional[int] = None, team_substr: Optional[str] = None) -> list[str]:
    """List pitcher names, optionally filtered by year/team."""
    return list_players("pitching", qualifier, year=year, team_substr=team_substr)
