"""Shared string normalizers for team, school, and player names.

These are pure functions with no data dependencies, so any module can import
them without pulling in pandas or the optional scraping extras.

This module is private. Nothing here is re-exported from ``ncaa_bbStats``.
"""

import re

__all__ = ["split_team_league", "strip_league"]


def split_team_league(team_league_str: str) -> tuple[str, str]:
    """Split an NCAA ``"Team Name (League)"`` label into its two parts.

    Only the final parenthesised group is treated as the league. Many schools
    carry a state disambiguator that is part of their identity -- there are two
    distinct programs named Anderson, Augustana, Bethel, Carroll, and Centenary,
    told apart only by ``(IN)`` vs ``(SC)``, ``(IL)`` vs ``(SD)``, and so on.
    Stripping every parenthesised group merges them.

    Args:
        team_league_str (str): A label such as ``"Miami (OH) (MAC)"``.

    Returns:
        tuple[str, str]: ``(team, league)``. The league is ``""`` when the label
        has no parenthesised suffix.

    Examples:
        >>> split_team_league("Northeastern (CAA)")
        ('Northeastern', 'CAA')
        >>> split_team_league("Miami (OH) (MAC)")
        ('Miami (OH)', 'MAC')
    """
    if "(" in team_league_str:
        team, league = team_league_str.rsplit("(", 1)
        return team.strip(), league.rstrip(")").strip()
    return team_league_str.strip(), ""


def strip_league(team_league_str: str) -> str:
    """Return just the team name from a ``"Team Name (League)"`` label.

    Args:
        team_league_str (str): A label such as ``"Augustana (SD) (NSIC)"``.

    Returns:
        str: The team name, keeping any state disambiguator.
    """
    return split_team_league(team_league_str)[0]


# Retained for callers that genuinely want every parenthesised group removed.
_ALL_PARENS = re.compile(r"\s*\(.*?\)")


def strip_all_parens(name: str) -> str:
    """Remove every parenthesised group from a name.

    Prefer :func:`strip_league` for NCAA team labels; this collapses schools
    that are distinguished only by a state suffix.

    Args:
        name (str): Any name.

    Returns:
        str: The name with all parenthesised groups removed.
    """
    return _ALL_PARENS.sub("", name).strip()
