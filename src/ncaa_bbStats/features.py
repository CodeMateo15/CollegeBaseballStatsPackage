"""The feature set the draft models are trained and scored on.

Single source of truth for feature *names and order*. Both the trainer and the
inference layer read from here, and the shipped model manifest records the list
so a mismatch fails loudly at load rather than producing confident garbage from
a silently permuted vector.

No feature depends on a third-party analytics provider. Where the reference
implementation used proprietary metrics, the package-derived equivalents from
:mod:`ncaa_bbStats.advanced_stats` stand in -- and since both are linear
functions of the same counting statistics, which are also features here, the
information content is unchanged.
"""

from typing import Literal, Optional

import pandas as pd

__all__ = [
    "PLAYER_FEATURES",
    "TEAM_FEATURES",
    "RPI_FEATURES",
    "FINANCE_FEATURES",
    "USAGE_FEATURES",
    "model_features",
    "add_usage_features",
    "ROLE_MAP",
]

Stage = Literal[1, 2]

#: Batting and pitching lines. Counting statistics plus the rates and
#: run-value metrics computed from them.
PLAYER_FEATURES = [
    "age", "role",
    # Pitching
    "w_pitch", "l_pitch", "g_pitch", "gs_pitch", "cg_pitch", "sho_pitch",
    "sv_pitch", "ip_pitch", "tbf_pitch", "h_pitch", "r_pitch", "er_pitch",
    "hr_pitch", "bb_pitch", "hbp_pitch", "wp_pitch", "bk_pitch", "so_pitch",
    "era_pitch", "whip_pitch", "k/9_pitch", "bb/9_pitch", "hr/9_pitch",
    "k/bb_pitch", "k%_pitch", "bb%_pitch", "k-bb%_pitch", "babip_pitch",
    "cfip_pitch", "clob%_pitch", "e-cf_pitch",
    # Batting
    "g_bat", "ab_bat", "pa_bat", "h_bat", "1b_bat", "2b_bat", "3b_bat",
    "hr_bat", "r_bat", "rbi_bat", "bb_bat", "so_bat", "hbp_bat", "sf_bat",
    "sh_bat", "gdp_bat", "sb_bat", "cs_bat", "tb_bat",
    "avg_bat", "obp_bat", "slg_bat", "ops_bat", "iso_bat", "babip_bat",
    "bb%_bat", "k%_bat", "bb/k_bat",
    "cwoba_bat", "cwraa_bat", "cwrc_bat", "cwrc+_bat", "cwsb_bat", "cspd_bat",
]

#: The player's program that season, from the NCAA team-stats cache.
TEAM_FEATURES = [
    "W_team", "L_team", "T_team", "G_team", "WPCT_team", "PE_team",
    "PE_pct_team",
    "BB (Batting)_team", "AB_team", "H_team", "BA_team", "DP_team",
    "DPPG_team", "2B_team", "2BPG_team", "IP_team", "R (Pitching)_team",
    "ER_team", "ERA_team", "PO_team", "A_team", "E_team", "FPCT_team",
    "HB_team", "HBP_team", "HA_team", "HAPG_team", "HR_team", "HRPG_team",
    "SF_team", "SH_team", "OBP_team", "SB_team", "SBPG_team", "CS_team",
    "R (Batting)_team", "RPG_team", "SHO_team", "TB_team", "SLG_team",
    "SO_team", "BB (Pitching)_team", "K/BB_team", "K/9_team", "TP_team",
    "3B_team", "3BPG_team", "WHIP_team", "BBPG (Pitching)_team",
]

#: Schedule strength and quality of opposition.
RPI_FEATURES = [
    "rpi_rank_team", "sos_rank_team",
    "conference_win_pct_team", "overall_win_pct_team",
    "nonconference_win_pct_team", "nonconference_rpi_rank_team",
    "home_win_pct_team", "road_win_pct_team", "neutral_win_pct_team",
    "q1_win_pct_team", "q2_win_pct_team", "q3_win_pct_team", "q4_win_pct_team",
    "q1_wins_team",
]

#: Program resources. Optional -- see the model card for the ablation result.
FINANCE_FEATURES = [
    "budget_pct_team", "log_budget_team", "opex_per_player_pct_team",
    "log_budget_per_player_team", "roster_size_team", "log_revenue_team",
    "net_revenue_team", "coaching_staff_size_team",
    "dept_recruiting_pct_team", "log_dept_coach_salary_team",
]

#: Playing-time shares. Without these the model has to learn the division of a
#: player's totals by their team's totals from scratch.
USAGE_FEATURES = [
    "ip_per_g_pitch", "start_share_pitch", "so_per_ip_pitch", "ip_share_pitch",
    "pa_per_g_bat", "g_share_bat", "ab_share_bat",
]

#: Biography from the draft record. Stage 2 only -- these are known for drafted
#: players, so using them in Stage 1 would leak the label.
BIO_FEATURES = [
    "api_height", "api_weight", "api_position", "api_bats", "api_throws",
]

ROLE_MAP = {"batter": 0, "pitcher": 1, "two_way": 2}


def add_usage_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add playing-time share features in place, returning the frame.

    Args:
        df (pandas.DataFrame): Rows carrying player and team totals.

    Returns:
        pandas.DataFrame: The same frame, with usage columns added.
    """
    def ratio(name, numerator, denominator):
        if numerator in df.columns and denominator in df.columns:
            df[name] = df[numerator] / df[denominator].replace(0, pd.NA)
        else:
            df[name] = pd.NA

    ratio("ip_per_g_pitch", "ip_pitch", "g_pitch")
    ratio("start_share_pitch", "gs_pitch", "g_pitch")
    ratio("so_per_ip_pitch", "so_pitch", "ip_pitch")
    ratio("ip_share_pitch", "ip_pitch", "IP_team")
    ratio("pa_per_g_bat", "pa_bat", "g_bat")
    ratio("g_share_bat", "g_bat", "G_team")
    ratio("ab_share_bat", "ab_bat", "AB_team")
    return df


def model_features(
    stage: Stage = 1, *, include_finance: bool = True
) -> list[str]:
    """The exact feature list, in order, for one model stage.

    Args:
        stage (int): 1 for the drafted/not-drafted classifier, 2 for the
            draft-order regressor.
        include_finance (bool): Include program-finance features.

    Returns:
        list[str]: Feature names in the order the model expects them.
    """
    features = list(PLAYER_FEATURES) + list(TEAM_FEATURES) + list(RPI_FEATURES)
    if include_finance:
        features += list(FINANCE_FEATURES)
    features += list(USAGE_FEATURES)
    if stage == 2:
        features += list(BIO_FEATURES)
    return features


def align(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Return `df` reindexed to exactly `features`, as float64.

    Missing columns become all-NaN, which is what the gradient-boosted models
    expect for an absent value. Extra columns are dropped.

    Every column is coerced with :func:`pandas.to_numeric`, which converts
    pandas' nullable ``NA`` to ``numpy.nan``. Without that, a column carrying
    ``NA`` raises ``TypeError: float() argument must be ... not 'NAType'`` at
    fit time -- and which columns are nullable depends on how the frame was
    assembled, so it is not reliably visible upstream.

    Args:
        df (pandas.DataFrame): Any frame.
        features (list[str]): The required columns, in order.

    Returns:
        pandas.DataFrame: Reindexed float64 copy.
    """
    aligned = df.reindex(columns=features)
    return aligned.apply(pd.to_numeric, errors="coerce").astype("float64")
