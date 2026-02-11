import uuid

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.formula.api as smf


def descriptive_stats(df: pd.DataFrame, value_col: str, group_col: str) -> list[dict]:
    out = []
    for group, sub in df.groupby(group_col):
        vals = sub[value_col].dropna()
        ci_low, ci_high = stats.t.interval(
            0.95,
            max(len(vals) - 1, 1),
            loc=np.mean(vals),
            scale=stats.sem(vals) if len(vals) > 1 else 0,
        )
        out.append(
            {
                "group": group,
                "n": int(len(vals)),
                "mean": float(np.mean(vals)),
                "median": float(np.median(vals)),
                "sd": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0,
                "ci95": [float(ci_low), float(ci_high)],
            }
        )
    return out


def run_analysis(df: pd.DataFrame, dependent: str, group: str) -> dict:
    result = {"run_id": str(uuid.uuid4())}
    result["descriptive"] = descriptive_stats(df, dependent, group)

    normality = {}
    for g, sub in df.groupby(group):
        if len(sub) >= 3:
            normality[g] = dict(zip(["statistic", "pvalue"], map(float, stats.shapiro(sub[dependent]))))
    result["normality"] = normality

    groups = [sub[dependent].values for _, sub in df.groupby(group)]
    if len(groups) == 2:
        t_stat, t_p = stats.ttest_ind(*groups, equal_var=False)
        u_stat, u_p = stats.mannwhitneyu(*groups, alternative="two-sided")
        pooled_sd = np.sqrt((np.var(groups[0], ddof=1) + np.var(groups[1], ddof=1)) / 2)
        cohen_d = (np.mean(groups[0]) - np.mean(groups[1])) / pooled_sd if pooled_sd > 0 else 0
        result["group_test"] = {
            "t_test": {"statistic": float(t_stat), "pvalue": float(t_p)},
            "mann_whitney": {"statistic": float(u_stat), "pvalue": float(u_p)},
            "effect_size": {"cohens_d": float(cohen_d)},
        }
    elif len(groups) > 2:
        f_stat, f_p = stats.f_oneway(*groups)
        kw_stat, kw_p = stats.kruskal(*groups)
        result["group_test"] = {
            "anova": {"statistic": float(f_stat), "pvalue": float(f_p)},
            "kruskal_wallis": {"statistic": float(kw_stat), "pvalue": float(kw_p)},
            "effect_size": {"eta_squared": float(f_stat / (f_stat + (len(df) - len(groups)))) if len(df) > len(groups) else 0},
        }

    if "participant_id" in df.columns and df.groupby("participant_id").size().max() > 1:
        model = smf.mixedlm(f"{dependent} ~ C({group})", df, groups=df["participant_id"])
        fit = model.fit()
        result["repeated_measures"] = {
            "method": "mixed_effects",
            "params": {k: float(v) for k, v in fit.params.to_dict().items()},
            "pvalues": {k: float(v) for k, v in fit.pvalues.to_dict().items()},
        }

    result["multiple_comparisons"] = "Use Holm-Bonferroni on post-hoc tests when >2 groups"
    return result
