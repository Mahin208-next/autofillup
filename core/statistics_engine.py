"""
Statistical analysis studio engine for SurveyForge AI.
Computes descriptive statistics, scale reliability (Cronbach's alpha),
bivariate correlations, hypothesis tests, and OLS regression.
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm


class StatisticsEngine:
    """Comprehensive statistical computing engine for academic survey research."""

    SYNTHETIC_WARNING = (
        "ACADEMIC NOTICE: This analysis is performed on a synthetic dataset. "
        "Observed statistical significance (p < 0.05) is a direct reflection of configured "
        "simulation parameters and mathematical latent-variable assumptions. "
        "It DOES NOT constitute empirical verification of real-world human behavior in Bangladesh."
    )

    @staticmethod
    def descriptive_stats(series: pd.Series) -> Dict[str, Any]:
        """Compute complete descriptive statistics for a numeric or categorical series."""
        clean = series.dropna()
        n = len(clean)
        missing = int(series.isna().sum())

        is_numeric = pd.api.types.is_numeric_dtype(clean)

        res = {
            "variable": series.name,
            "sample_size": n,
            "missing_count": missing,
            "missing_pct": round((missing / len(series) * 100), 2) if len(series) > 0 else 0.0,
            "is_numeric": is_numeric
        }

        if is_numeric and n > 0:
            res.update({
                "mean": round(float(clean.mean()), 3),
                "median": round(float(clean.median()), 3),
                "mode": round(float(clean.mode().iloc[0]), 3) if not clean.mode().empty else None,
                "std": round(float(clean.std()), 3),
                "variance": round(float(clean.var()), 3),
                "min": round(float(clean.min()), 3),
                "max": round(float(clean.max()), 3),
                "skewness": round(float(stats.skew(clean)), 3) if n > 2 else None,
                "kurtosis": round(float(stats.kurtosis(clean)), 3) if n > 3 else None
            })
        else:
            # Frequency table for categorical series
            freq = clean.value_counts()
            pct = clean.value_counts(normalize=True) * 100.0
            freq_df = pd.DataFrame({"Count": freq, "Percentage (%)": pct.round(2)})
            res["frequency_table"] = freq_df

        return res

    @staticmethod
    def cronbach_alpha(df: pd.DataFrame, items: List[str]) -> Dict[str, Any]:
        """
        Calculates Cronbach's Alpha and Corrected Item-Total Correlations.
        df: DataFrame containing survey questions.
        items: List of column names representing scale items.
        """
        sub_df = df[items].apply(pd.to_numeric, errors="coerce").dropna()
        k = len(items)
        n = len(sub_df)

        if k < 2 or n < 3:
            return {
                "alpha": 0.0,
                "interpretation": "Insufficient items or sample size for Cronbach's Alpha (minimum 2 items required).",
                "item_total_correlations": {},
                "n_items": k,
                "sample_size": n
            }

        item_vars = sub_df.var(axis=0, ddof=1)
        total_var = sub_df.sum(axis=1).var(ddof=1)

        if total_var == 0:
            alpha = 0.0
        else:
            alpha = (k / (k - 1)) * (1 - (item_vars.sum() / total_var))

        alpha = float(np.clip(alpha, 0.0, 1.0))

        # Item-total correlation and alpha-if-item-deleted
        item_total_stats = []
        total_score = sub_df.sum(axis=1)

        for col in items:
            score_without_item = total_score - sub_df[col]
            corr, _ = stats.pearsonr(sub_df[col], score_without_item)

            # Alpha if item deleted
            remaining = [c for c in items if c != col]
            if len(remaining) >= 2:
                rem_vars = sub_df[remaining].var(axis=0, ddof=1)
                rem_tot = sub_df[remaining].sum(axis=1).var(ddof=1)
                alpha_del = (len(remaining) / (len(remaining) - 1)) * (1 - (rem_vars.sum() / rem_tot)) if rem_tot > 0 else 0.0
            else:
                alpha_del = 0.0

            item_total_stats.append({
                "Item": col,
                "Mean": round(float(sub_df[col].mean()), 3),
                "Std Dev": round(float(sub_df[col].std()), 3),
                "Corrected Item-Total Correlation": round(float(corr), 3),
                "Alpha If Item Deleted": round(float(np.clip(alpha_del, 0.0, 1.0)), 3)
            })

        # Quality benchmark
        if alpha >= 0.85:
            interp = f"High internal consistency (Alpha = {alpha:.3f})."
        elif alpha >= 0.70:
            interp = f"Acceptable academic scale reliability (Alpha = {alpha:.3f})."
        elif alpha >= 0.60:
            interp = f"Questionable internal consistency (Alpha = {alpha:.3f}). Items may require refinement."
        else:
            interp = f"Poor reliability (Alpha = {alpha:.3f}). Scale lacks coherence."

        return {
            "test_name": "Cronbach's Alpha Reliability Analysis",
            "alpha": round(alpha, 3),
            "sample_size": n,
            "n_items": k,
            "interpretation": interp,
            "item_table": pd.DataFrame(item_total_stats),
            "limitations": "Reliability coefficients reflect synthetic item correlation structure. " + StatisticsEngine.SYNTHETIC_WARNING
        }

    @staticmethod
    def correlation_analysis(
        df: pd.DataFrame,
        cols: List[str],
        method: str = "pearson"
    ) -> Dict[str, Any]:
        """Compute bivariate correlation matrix with p-values."""
        sub_df = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
        n = len(sub_df)

        corr_mat = pd.DataFrame(index=cols, columns=cols, dtype=float)
        pval_mat = pd.DataFrame(index=cols, columns=cols, dtype=float)

        for c1 in cols:
            for c2 in cols:
                if c1 == c2:
                    corr_mat.loc[c1, c2] = 1.0
                    pval_mat.loc[c1, c2] = 0.0
                else:
                    if method == "spearman":
                        r, p = stats.spearmanr(sub_df[c1], sub_df[c2])
                    else:
                        r, p = stats.pearsonr(sub_df[c1], sub_df[c2])
                    corr_mat.loc[c1, c2] = round(float(r), 3)
                    pval_mat.loc[c1, c2] = round(float(p), 4)

        return {
            "test_name": f"{method.capitalize()} Correlation Matrix",
            "method": method,
            "sample_size": n,
            "correlation_matrix": corr_mat,
            "p_values_matrix": pval_mat,
            "interpretation": f"Calculated {method.capitalize()} correlation across {len(cols)} variables.",
            "limitations": StatisticsEngine.SYNTHETIC_WARNING
        }

    @staticmethod
    def t_test_independent(
        df: pd.DataFrame,
        num_col: str,
        group_col: str
    ) -> Dict[str, Any]:
        """Perform two-sample independent T-test with Levene's test for variance."""
        sub = df[[num_col, group_col]].dropna()
        groups = sub[group_col].unique()

        if len(groups) != 2:
            return {"error": f"Group variable '{group_col}' must have exactly 2 distinct groups. Found: {len(groups)}"}

        g1 = pd.to_numeric(sub[sub[group_col] == groups[0]][num_col], errors="coerce").dropna()
        g2 = pd.to_numeric(sub[sub[group_col] == groups[1]][num_col], errors="coerce").dropna()

        # Levene's test for equality of variances
        stat_lev, p_lev = stats.levene(g1, g2)
        equal_var = p_lev >= 0.05

        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=equal_var)

        # Cohen's d effect size
        n1, n2 = len(g1), len(g2)
        s1, s2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2)) if (n1 + n2 - 2) > 0 else 1.0
        cohens_d = (np.mean(g1) - np.mean(g2)) / pooled_std if pooled_std > 0 else 0.0

        interp = (
            f"Comparing {groups[0]} (M = {g1.mean():.2f}, SD = {g1.std():.2f}) "
            f"and {groups[1]} (M = {g2.mean():.2f}, SD = {g2.std():.2f}): "
            f"t({n1+n2-2}) = {t_stat:.3f}, p = {p_val:.4f}. "
            f"Effect size (Cohen's d) = {cohens_d:.2f}."
        )

        return {
            "test_name": "Independent Samples T-Test",
            "num_var": num_col,
            "group_var": group_col,
            "groups": [str(groups[0]), str(groups[1])],
            "sample_size": n1 + n2,
            "test_statistic": round(float(t_stat), 3),
            "p_value": round(float(p_val), 4),
            "cohens_d": round(float(cohens_d), 3),
            "equal_variance_assumed": equal_var,
            "levene_p_value": round(float(p_lev), 4),
            "group_summary": pd.DataFrame({
                "Group": [str(groups[0]), str(groups[1])],
                "N": [n1, n2],
                "Mean": [round(float(g1.mean()), 3), round(float(g2.mean()), 3)],
                "SD": [round(float(g1.std()), 3), round(float(g2.std()), 3)]
            }),
            "interpretation": interp,
            "limitations": StatisticsEngine.SYNTHETIC_WARNING
        }

    @staticmethod
    def t_test_paired(
        df: pd.DataFrame,
        col1: str,
        col2: str
    ) -> Dict[str, Any]:
        """Perform paired samples T-test comparing two continuous measures on the same subjects."""
        sub = df[[col1, col2]].apply(pd.to_numeric, errors="coerce").dropna()
        n = len(sub)

        if n < 3:
            return {"error": "Insufficient paired observations to compute paired T-test."}

        v1 = sub[col1]
        v2 = sub[col2]
        diff = v1 - v2
        mean_diff = float(diff.mean())
        std_diff = float(diff.std(ddof=1))

        t_stat, p_val = stats.ttest_rel(v1, v2)
        cohens_dz = mean_diff / std_diff if std_diff > 0 else 0.0

        interp = (
            f"Paired T-test comparing '{col1}' (M = {v1.mean():.2f}) and '{col2}' (M = {v2.mean():.2f}): "
            f"Mean Difference = {mean_diff:.2f}, t({n-1}) = {t_stat:.3f}, p = {p_val:.4f}, "
            f"Cohen's dz = {cohens_dz:.2f}."
        )

        return {
            "test_name": "Paired Samples T-Test",
            "variables": [col1, col2],
            "sample_size": n,
            "test_statistic": round(float(t_stat), 3),
            "p_value": round(float(p_val), 4),
            "mean_difference": round(mean_diff, 3),
            "cohens_d": round(cohens_dz, 3),
            "group_summary": pd.DataFrame({
                "Variable": [col1, col2, "Difference"],
                "Mean": [round(float(v1.mean()), 3), round(float(v2.mean()), 3), round(mean_diff, 3)],
                "SD": [round(float(v1.std()), 3), round(float(v2.std()), 3), round(std_diff, 3)]
            }),
            "interpretation": interp,
            "limitations": StatisticsEngine.SYNTHETIC_WARNING
        }

    @staticmethod
    def anova_one_way(
        df: pd.DataFrame,
        num_col: str,
        group_col: str
    ) -> Dict[str, Any]:
        """Perform One-Way ANOVA across multiple categorical groups."""
        sub = df[[num_col, group_col]].dropna()
        group_vals = sub[group_col].unique()

        if len(group_vals) < 2:
            return {"error": f"Group variable must contain at least 2 distinct levels. Found: {len(group_vals)}"}

        samples = [pd.to_numeric(sub[sub[group_col] == g][num_col], errors="coerce").dropna() for g in group_vals]
        # Filter groups with at least 2 observations
        valid_samples = [s for s in samples if len(s) >= 2]

        if len(valid_samples) < 2:
            return {"error": "Not enough data points in each group to compute ANOVA."}

        f_stat, p_val = stats.f_oneway(*valid_samples)

        # Eta-squared effect size
        all_vals = np.concatenate(valid_samples)
        grand_mean = np.mean(all_vals)
        ss_between = sum(len(s) * (np.mean(s) - grand_mean) ** 2 for s in valid_samples)
        ss_total = sum((x - grand_mean) ** 2 for x in all_vals)
        eta_sq = ss_between / ss_total if ss_total > 0 else 0.0

        group_summary_rows = []
        for g, s in zip(group_vals, samples):
            group_summary_rows.append({
                "Group": str(g),
                "N": len(s),
                "Mean": round(float(s.mean()), 3) if len(s) > 0 else 0,
                "Std Dev": round(float(s.std()), 3) if len(s) > 1 else 0
            })

        interp = (
            f"One-way ANOVA test for differences in '{num_col}' across '{group_col}' "
            f"yielded F = {f_stat:.3f}, p = {p_val:.4f}. "
            f"Eta-squared (η²) = {eta_sq:.3f}."
        )

        return {
            "test_name": "One-Way ANOVA",
            "num_var": num_col,
            "group_var": group_col,
            "sample_size": len(all_vals),
            "test_statistic": round(float(f_stat), 3),
            "p_value": round(float(p_val), 4),
            "eta_squared": round(float(eta_sq), 3),
            "group_summary": pd.DataFrame(group_summary_rows),
            "interpretation": interp,
            "limitations": StatisticsEngine.SYNTHETIC_WARNING
        }

    @staticmethod
    def chi_square_test(
        df: pd.DataFrame,
        col1: str,
        col2: str
    ) -> Dict[str, Any]:
        """Perform Chi-Square Test of Independence with contingency table and Cramer's V."""
        sub = df[[col1, col2]].dropna()
        if len(sub) < 5:
            return {"error": "Sample size too small for Chi-Square test."}

        contingency = pd.crosstab(sub[col1], sub[col2])
        chi2, p_val, dof, expected = stats.chi2_contingency(contingency)

        # Cramer's V
        n = contingency.sum().sum()
        min_dim = min(contingency.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if (n > 0 and min_dim > 0) else 0.0

        interp = (
            f"Chi-Square test of independence between '{col1}' and '{col2}': "
            f"χ²({dof}) = {chi2:.3f}, p = {p_val:.4f}. "
            f"Cramer's V = {cramers_v:.3f}."
        )

        return {
            "test_name": "Chi-Square Test of Independence",
            "variables": [col1, col2],
            "sample_size": int(n),
            "test_statistic": round(float(chi2), 3),
            "p_value": round(float(p_val), 4),
            "degrees_of_freedom": int(dof),
            "cramers_v": round(float(cramers_v), 3),
            "contingency_table": contingency,
            "interpretation": interp,
            "limitations": StatisticsEngine.SYNTHETIC_WARNING
        }

    @staticmethod
    def linear_regression(
        df: pd.DataFrame,
        y_col: str,
        x_cols: List[str]
    ) -> Dict[str, Any]:
        """Perform Ordinary Least Squares (OLS) Linear Regression."""
        sub = df[[y_col] + x_cols].apply(pd.to_numeric, errors="coerce").dropna()
        n = len(sub)

        if n < len(x_cols) + 2:
            return {"error": f"Insufficient sample size (N={n}) for {len(x_cols)} predictor variables."}

        Y = sub[y_col]
        X = sm.add_constant(sub[x_cols])

        model = sm.OLS(Y, X).fit()

        coef_table = []
        for var in model.params.index:
            coef_table.append({
                "Variable": var,
                "Coefficient": round(float(model.params[var]), 4),
                "Std Error": round(float(model.bse[var]), 4),
                "t-statistic": round(float(model.tvalues[var]), 3),
                "p-value": round(float(model.pvalues[var]), 4),
                "95% CI Lower": round(float(model.conf_int().loc[var, 0]), 4),
                "95% CI Upper": round(float(model.conf_int().loc[var, 1]), 4)
            })

        interp = (
            f"OLS model for dependent variable '{y_col}': "
            f"R² = {model.rsquared:.3f}, Adjusted R² = {model.rsquared_adj:.3f}, "
            f"F({int(model.df_model)}, {int(model.df_resid)}) = {model.fvalue:.2f}, p = {model.f_pvalue:.4f}."
        )

        return {
            "test_name": "Multiple Linear Regression (OLS)" if len(x_cols) > 1 else "Simple Linear Regression (OLS)",
            "dependent_variable": y_col,
            "independent_variables": x_cols,
            "sample_size": n,
            "r_squared": round(float(model.rsquared), 3),
            "r_squared_adj": round(float(model.rsquared_adj), 3),
            "f_statistic": round(float(model.fvalue), 3) if model.fvalue is not None else None,
            "p_value": round(float(model.f_pvalue), 4) if model.f_pvalue is not None else None,
            "coefficients_table": pd.DataFrame(coef_table),
            "interpretation": interp,
            "limitations": StatisticsEngine.SYNTHETIC_WARNING
        }

