"""
Statistical Analysis Studio Page for SurveyForge AI.
Computes descriptive statistics, Cronbach's alpha, bivariate correlations,
hypothesis tests (t-tests, ANOVA, Chi-Square), and OLS linear regression models.
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from database.db import SessionLocal
from database.models import Project, SyntheticDataset, AnalysisResult, ResearchVariable
from core.statistics_engine import StatisticsEngine


def render():
    st.markdown("<div class='section-header'><h2>📈 Statistical Analysis Studio</h2><p>Execute inferential hypothesis tests, psychometric reliability analysis, and regression modeling.</p></div>", unsafe_allow_html=True)

    project_id = st.session_state.get("current_project_id")

    db = SessionLocal()
    try:
        datasets = (
            db.query(SyntheticDataset)
            .filter(SyntheticDataset.project_id == project_id)
            .order_by(SyntheticDataset.id.desc())
            .all()
        )

        r_vars = db.query(ResearchVariable).filter(ResearchVariable.project_id == project_id).all()

        if not datasets:
            st.info("No synthetic datasets available to analyze. Please generate a dataset first.")
            return

        ds_map = {ds.id: f"#{ds.id} — {ds.name} (N={ds.record_count})" for ds in datasets}
        selected_ds_id = st.selectbox("Active Analysis Dataset", options=list(ds_map.keys()), format_func=lambda x: ds_map[x])
        target_ds = db.query(SyntheticDataset).filter(SyntheticDataset.id == selected_ds_id).first()

    finally:
        db.close()

    if not Path(target_ds.file_path).exists():
        st.error(f"Dataset file missing from disk: {target_ds.file_path}")
        return

    df = pd.read_csv(target_ds.file_path)

    # Disclose synthetic limitation
    st.warning(f"⚠️ {StatisticsEngine.SYNTHETIC_WARNING}")

    # Tabs for methods
    tab_desc, tab_rel, tab_corr, tab_hyp, tab_reg, tab_history = st.tabs([
        "📊 Descriptive Statistics",
        "📐 Reliability (Cronbach's α)",
        "🔗 Bivariate Correlations",
        "🧪 Hypothesis Testing (T-Test/ANOVA/χ²)",
        "📈 Regression Modeling (OLS)",
        "📜 Analysis History & Reports"
    ])

    # TAB 1: Descriptive
    with tab_desc:
        st.markdown("#### Descriptive Statistics")
        var_choice = st.selectbox("Select Variable to Analyze", options=[c for c in df.columns if c != "data_type"])

        desc_res = StatisticsEngine.descriptive_stats(df[var_choice])

        if desc_res["is_numeric"]:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Sample Size (N)", desc_res["sample_size"])
            c2.metric("Mean", desc_res["mean"])
            c3.metric("Std Dev (SD)", desc_res["std"])
            c4.metric("Median", desc_res["median"])

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Min", desc_res["min"])
            c6.metric("Max", desc_res["max"])
            c7.metric("Skewness", desc_res["skewness"])
            c8.metric("Missing %", f"{desc_res['missing_pct']}%")
        else:
            st.markdown("##### Frequency Breakdown")
            st.dataframe(desc_res.get("frequency_table"), use_container_width=True)

    # TAB 2: Reliability
    with tab_rel:
        st.markdown("#### Psychometric Scale Reliability (Cronbach's Alpha)")
        st.write("Calculate internal consistency across multiple Likert items or survey questions.")

        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors="coerce")) and c not in ("synthetic_record_id", "generation_seed")]

        # Pre-select Likert items if available
        likert_candidates = [c for c in numeric_cols if ("trust" in c.lower() or "risk" in c.lower() or "verif" in c.lower()) and "comp_" not in c.lower()]
        default_items = likert_candidates[:4] if len(likert_candidates) >= 2 else numeric_cols[:3]

        selected_scale_items = st.multiselect("Select Scale Items (min 2 items)", options=numeric_cols, default=default_items)

        if st.button("Calculate Scale Reliability"):
            if len(selected_scale_items) < 2:
                st.error("Please select at least 2 items to compute Cronbach's Alpha.")
            else:
                rel_res = StatisticsEngine.cronbach_alpha(df, selected_scale_items)

                c_a1, c_a2 = st.columns([1, 2])
                with c_a1:
                    alpha_val = rel_res["alpha"]
                    color = "#10b981" if alpha_val >= 0.70 else "#f59e0b"
                    st.markdown(
                        f"""
                        <div style="background: #ffffff; border: 2px solid {color}; border-radius: 8px; padding: 1.5rem; text-align: center;">
                            <div style="font-size: 0.85rem; color: #64748b; font-weight: 600;">CRONBACH'S ALPHA (α)</div>
                            <div style="font-size: 2.8rem; font-weight: 800; color: {color};">{alpha_val:.3f}</div>
                            <div style="font-size: 0.82rem; color: #334155; margin-top: 0.5rem;">{rel_res['interpretation']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with c_a2:
                    st.markdown("##### Item-Total Statistics & Sensitivity")
                    st.dataframe(rel_res.get("item_table"), use_container_width=True, hide_index=True)

                _save_analysis_to_db(project_id, target_ds.id, rel_res, selected_scale_items)

    # TAB 3: Correlation
    with tab_corr:
        st.markdown("#### Bivariate Correlation Matrix")
        corr_method = st.radio("Correlation Method", options=["pearson", "spearman"], horizontal=True)

        corr_candidates = [c for c in numeric_cols if "id" not in c.lower() and "seed" not in c.lower()]
        selected_corr_vars = st.multiselect(
            "Select Variables for Matrix",
            options=corr_candidates,
            default=corr_candidates[:6]
        )

        if st.button("Compute Correlation Matrix"):
            if len(selected_corr_vars) < 2:
                st.error("Please select at least 2 variables.")
            else:
                corr_res = StatisticsEngine.correlation_analysis(df, selected_corr_vars, method=corr_method)
                st.markdown("##### Correlation Coefficients (r)")
                st.dataframe(corr_res["correlation_matrix"].style.background_gradient(cmap="coolwarm", vmin=-1.0, vmax=1.0), use_container_width=True)

                st.markdown("##### P-Values Matrix (Significance)")
                st.dataframe(corr_res["p_values_matrix"], use_container_width=True)

                _save_analysis_to_db(project_id, target_ds.id, corr_res, selected_corr_vars)

    # TAB 4: Hypothesis Testing
    with tab_hyp:
        st.markdown("#### Inferential Hypothesis Testing")
        test_type = st.selectbox(
            "Select Hypothesis Test",
            options=["Independent Samples T-Test", "Paired Samples T-Test", "One-Way ANOVA", "Chi-Square Test of Independence"]
        )

        if test_type == "Independent Samples T-Test":
            st.markdown("##### Compare Continuous Dependent Variable across 2 Independent Groups")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                t_num = st.selectbox("Continuous Variable (DV)", options=numeric_cols, index=0)
            with col_t2:
                # Find binary categorical columns
                cat_cols = [c for c in df.columns if c not in numeric_cols and c not in ("synthetic_record_id", "generation_timestamp")]
                binary_cols = [c for c in cat_cols if df[c].nunique() == 2] or cat_cols
                t_grp = st.selectbox("Grouping Variable (2 levels)", options=binary_cols if binary_cols else [c for c in df.columns])

            if st.button("Run Independent T-Test"):
                res = StatisticsEngine.t_test_independent(df, t_num, t_grp)
                if "error" in res:
                    st.error(res["error"])
                else:
                    _display_test_results(res)
                    _save_analysis_to_db(project_id, target_ds.id, res, [t_num, t_grp])

        elif test_type == "Paired Samples T-Test":
            st.markdown("##### Compare Two Continuous Measures on the Same Respondents")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_var1 = st.selectbox("Measure 1 (e.g. Trust in AI)", options=numeric_cols, index=0)
            with col_p2:
                p_var2 = st.selectbox("Measure 2 (e.g. Trust in Social Media)", options=numeric_cols, index=min(1, len(numeric_cols)-1))

            if st.button("Run Paired Samples T-Test"):
                res = StatisticsEngine.t_test_paired(df, p_var1, p_var2)
                if "error" in res:
                    st.error(res["error"])
                else:
                    _display_test_results(res)
                    _save_analysis_to_db(project_id, target_ds.id, res, [p_var1, p_var2])

        elif test_type == "One-Way ANOVA":
            st.markdown("##### Compare Continuous Variable across 3+ Categorical Levels")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                a_num = st.selectbox("Dependent Continuous Variable", options=numeric_cols, index=0)
            with col_a2:
                cat_cols = [c for c in df.columns if c not in numeric_cols and c not in ("synthetic_record_id", "generation_timestamp")]
                a_grp = st.selectbox("Categorical Factor", options=cat_cols if cat_cols else list(df.columns))

            if st.button("Run One-Way ANOVA"):
                res = StatisticsEngine.anova_one_way(df, a_num, a_grp)
                if "error" in res:
                    st.error(res["error"])
                else:
                    _display_test_results(res)
                    _save_analysis_to_db(project_id, target_ds.id, res, [a_num, a_grp])

        elif test_type == "Chi-Square Test of Independence":
            st.markdown("##### Test Association between Two Categorical Survey Questions")
            c_cols = [c for c in df.columns if c not in ("synthetic_record_id", "generation_timestamp")]
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                c1 = st.selectbox("Categorical Variable 1", options=c_cols, index=0)
            with col_c2:
                c2 = st.selectbox("Categorical Variable 2", options=c_cols, index=min(1, len(c_cols)-1))

            if st.button("Run Chi-Square Test"):
                res = StatisticsEngine.chi_square_test(df, c1, c2)
                if "error" in res:
                    st.error(res["error"])
                else:
                    _display_test_results(res)
                    _save_analysis_to_db(project_id, target_ds.id, res, [c1, c2])

    # TAB 5: Regression
    with tab_reg:
        st.markdown("#### Ordinary Least Squares (OLS) Regression")
        r_y = st.selectbox("Dependent Outcome Variable (Y)", options=numeric_cols, index=min(len(numeric_cols)-1, 4))
        remaining_num = [c for c in numeric_cols if c != r_y]
        r_x = st.multiselect("Independent Predictor Variables (X)", options=remaining_num, default=remaining_num[:3])

        if st.button("Fit OLS Regression Model"):
            if not r_x:
                st.error("Select at least one predictor variable (X).")
            else:
                reg_res = StatisticsEngine.linear_regression(df, r_y, r_x)
                if "error" in reg_res:
                    st.error(reg_res["error"])
                else:
                    st.markdown("##### Model Summary & Goodness-of-Fit")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("R-Squared (R²)", f"{reg_res['r_squared']:.3f}")
                    m2.metric("Adjusted R²", f"{reg_res['r_squared_adj']:.3f}")
                    m3.metric("F-Statistic", f"{reg_res['f_statistic']:.2f}" if reg_res['f_statistic'] else "N/A")
                    m4.metric("Model p-value", f"{reg_res['p_value']:.4f}" if reg_res['p_value'] else "N/A")

                    st.markdown("##### Coefficients & Parameter Estimates")
                    st.dataframe(reg_res["coefficients_table"], use_container_width=True, hide_index=True)

                    st.info(f"**Interpretation:** {reg_res['interpretation']}")
                    _save_analysis_to_db(project_id, target_ds.id, reg_res, [r_y] + r_x)

    # TAB 6: History
    with tab_history:
        st.markdown("#### Saved Statistical Results for this Project")
        db = SessionLocal()
        try:
            saved = (
                db.query(AnalysisResult)
                .filter(AnalysisResult.project_id == project_id)
                .order_by(AnalysisResult.id.desc())
                .all()
            )
            if saved:
                history_rows = []
                for s in saved:
                    history_rows.append({
                        "Test": s.test_name,
                        "Sample N": s.sample_size,
                        "Statistic": f"{s.test_statistic:.3f}" if s.test_statistic is not None else "N/A",
                        "p-value": f"{s.p_value:.4f}" if s.p_value is not None else "N/A",
                        "Date": s.created_at.strftime("%Y-%m-%d %H:%M"),
                        "Interpretation": s.interpretation
                    })
                st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
            else:
                st.write("No statistical tests logged yet.")
        finally:
            db.close()


def _display_test_results(res: dict):
    """Helper to display formatted hypothesis test results."""
    st.markdown(f"##### Test Results: {res.get('test_name')}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Test Statistic", f"{res.get('test_statistic', 0.0):.3f}")
    c2.metric("p-value", f"{res.get('p_value', 1.0):.4f}")
    if "cohens_d" in res:
        c3.metric("Cohen's d (Effect)", f"{res['cohens_d']:.3f}")
    elif "eta_squared" in res:
        c3.metric("Eta-Squared (η²)", f"{res['eta_squared']:.3f}")
    elif "cramers_v" in res:
        c3.metric("Cramer's V", f"{res['cramers_v']:.3f}")

    if "group_summary" in res:
        st.dataframe(res["group_summary"], use_container_width=True, hide_index=True)
    if "contingency_table" in res:
        st.dataframe(res["contingency_table"], use_container_width=True)

    st.success(f"**Academic Interpretation:** {res.get('interpretation')}")


def _save_analysis_to_db(project_id: int, dataset_id: int, res: dict, variables: list):
    """Persist statistical result to database."""
    db = SessionLocal()
    try:
        obj = AnalysisResult(
            project_id=project_id,
            dataset_id=dataset_id,
            test_name=res.get("test_name", "Statistical Test"),
            variables_used=json.dumps(variables),
            sample_size=res.get("sample_size", 0),
            test_statistic=res.get("test_statistic") or res.get("alpha"),
            p_value=res.get("p_value"),
            metrics_json=json.dumps(res, default=str),
            interpretation=res.get("interpretation", ""),
            limitations=res.get("limitations", "")
        )
        db.add(obj)
        db.commit()
    except Exception as e:
        print(f"Error saving analysis: {e}")
    finally:
        db.close()

