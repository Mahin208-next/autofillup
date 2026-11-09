"""
Tests for Statistical Analysis Studio Engine.
"""
import pytest
import numpy as np
import pandas as pd
from core.statistics_engine import StatisticsEngine


@pytest.fixture
def stats_dataframe():
    rng = np.random.default_rng(42)
    n = 100
    x1 = rng.normal(3.0, 1.0, size=n)
    x2 = rng.normal(3.5, 0.8, size=n)
    # y depends on x1 and x2
    y = 0.5 * x1 + 0.3 * x2 + rng.normal(0, 0.5, size=n)
    group = rng.choice(["Group A", "Group B"], size=n)
    cat2 = rng.choice(["Yes", "No"], size=n)

    # Correlated scale items for Cronbach alpha
    latent = rng.normal(3.0, 0.8, size=n)
    item1 = np.clip(np.round(latent + rng.normal(0, 0.3, size=n)), 1, 5)
    item2 = np.clip(np.round(latent + rng.normal(0, 0.3, size=n)), 1, 5)
    item3 = np.clip(np.round(latent + rng.normal(0, 0.3, size=n)), 1, 5)

    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "group": group,
        "cat2": cat2,
        "item1": item1,
        "item2": item2,
        "item3": item3
    })


def test_descriptive_stats(stats_dataframe):
    """Verify descriptive statistics computation."""
    res_num = StatisticsEngine.descriptive_stats(stats_dataframe["y"])
    assert res_num["is_numeric"] is True
    assert "mean" in res_num
    assert "std" in res_num
    assert "median" in res_num
    assert res_num["sample_size"] == 100

    res_cat = StatisticsEngine.descriptive_stats(stats_dataframe["group"])
    assert res_cat["is_numeric"] is False
    assert "frequency_table" in res_cat
    assert len(res_cat["frequency_table"]) == 2


def test_cronbach_alpha(stats_dataframe):
    """Verify Cronbach's Alpha and item-total correlation calculation."""
    res = StatisticsEngine.cronbach_alpha(stats_dataframe, ["item1", "item2", "item3"])
    assert "alpha" in res
    assert 0.0 <= res["alpha"] <= 1.0
    assert res["alpha"] > 0.60  # Highly correlated scale items
    assert res["n_items"] == 3
    assert len(res["item_table"]) == 3
    assert "Corrected Item-Total Correlation" in res["item_table"].columns


def test_correlation_matrix(stats_dataframe):
    """Verify Pearson and Spearman correlation matrices."""
    res_p = StatisticsEngine.correlation_analysis(stats_dataframe, ["y", "x1", "x2"], method="pearson")
    assert res_p["correlation_matrix"].shape == (3, 3)
    assert res_p["correlation_matrix"].loc["x1", "x1"] == 1.0
    assert "p_values_matrix" in res_p

    res_s = StatisticsEngine.correlation_analysis(stats_dataframe, ["y", "x1", "x2"], method="spearman")
    assert res_s["correlation_matrix"].shape == (3, 3)


def test_independent_t_test(stats_dataframe):
    """Verify independent samples t-test."""
    res = StatisticsEngine.t_test_independent(stats_dataframe, "y", "group")
    assert "test_statistic" in res
    assert "p_value" in res
    assert "cohens_d" in res
    assert res["sample_size"] == 100


def test_paired_t_test(stats_dataframe):
    """Verify paired samples t-test."""
    res = StatisticsEngine.t_test_paired(stats_dataframe, "item1", "item2")
    assert "test_statistic" in res
    assert "p_value" in res
    assert "mean_difference" in res
    assert res["sample_size"] == 100


def test_anova_one_way(stats_dataframe):
    """Verify One-Way ANOVA."""
    res = StatisticsEngine.anova_one_way(stats_dataframe, "y", "group")
    assert "test_statistic" in res
    assert "p_value" in res
    assert "eta_squared" in res


def test_chi_square_test(stats_dataframe):
    """Verify Chi-Square test of independence."""
    res = StatisticsEngine.chi_square_test(stats_dataframe, "group", "cat2")
    assert "test_statistic" in res
    assert "p_value" in res
    assert "degrees_of_freedom" in res
    assert "contingency_table" in res


def test_linear_regression(stats_dataframe):
    """Verify OLS multiple linear regression."""
    res = StatisticsEngine.linear_regression(stats_dataframe, "y", ["x1", "x2"])
    assert "r_squared" in res
    assert "coefficients_table" in res
    assert res["r_squared"] > 0.20
    assert len(res["coefficients_table"]) == 3  # const, x1, x2

