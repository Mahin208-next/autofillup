"""
Visualization Studio Page for SurveyForge AI.
Interactive academic charting studio powered by Plotly (Bar, Pie, Hist, Box, Scatter, Heatmap).
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from database.db import SessionLocal
from database.models import Project, SyntheticDataset
from core.visualization_engine import VisualizationEngine


def render():
    st.markdown("<div class='section-header'><h2>📉 Visualization Studio</h2><p>Interactive Plotly charting studio for survey variable distributions, comparisons, and correlations.</p></div>", unsafe_allow_html=True)

    project_id = st.session_state.get("current_project_id")

    db = SessionLocal()
    try:
        datasets = (
            db.query(SyntheticDataset)
            .filter(SyntheticDataset.project_id == project_id)
            .order_by(SyntheticDataset.id.desc())
            .all()
        )

        if not datasets:
            st.info("No datasets available for visualization. Please generate a synthetic dataset first.")
            return

        ds_map = {ds.id: f"#{ds.id} — {ds.name} (N={ds.record_count})" for ds in datasets}
        selected_ds_id = st.selectbox("Select Dataset to Visualize", options=list(ds_map.keys()), format_func=lambda x: ds_map[x])
        target_ds = db.query(SyntheticDataset).filter(SyntheticDataset.id == selected_ds_id).first()

    finally:
        db.close()

    if not Path(target_ds.file_path).exists():
        st.error(f"Dataset file missing from disk: {target_ds.file_path}")
        return

    df = pd.read_csv(target_ds.file_path)

    survey_cols = [c for c in df.columns if c not in ("synthetic_record_id", "data_type", "generation_timestamp", "generation_seed")]
    numeric_cols = [c for c in survey_cols if pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors="coerce"))]
    cat_cols = [c for c in survey_cols if c not in numeric_cols]

    col_ctrl1, col_ctrl2 = st.columns([1, 2])

    with col_ctrl1:
        st.markdown("#### 🛠️ Chart Builder")
        chart_type = st.selectbox(
            "Chart Type",
            options=[
                "Bar Chart (Frequencies & %)",
                "Pie / Donut Chart",
                "Histogram (Spread & Density)",
                "Box & Whisker Plot",
                "Scatter Plot (with OLS Trendline)",
                "Correlation Heatmap Matrix"
            ]
        )

        chart_title = st.text_input("Custom Chart Title", placeholder="Leave blank for automatic title")

        if chart_type in ("Bar Chart (Frequencies & %)", "Pie / Donut Chart"):
            chosen_var = st.selectbox("Categorical / Survey Variable", options=survey_cols)
        elif chart_type == "Histogram (Spread & Density)":
            chosen_var = st.selectbox("Numeric Variable", options=numeric_cols if numeric_cols else survey_cols)
            bins = st.slider("Number of Bins", min_value=5, max_value=50, value=15)
        elif chart_type == "Box & Whisker Plot":
            y_var = st.selectbox("Dependent / Continuous (Y-axis)", options=numeric_cols if numeric_cols else survey_cols)
            x_var = st.selectbox("Grouping Factor (X-axis, Optional)", options=["None"] + survey_cols)
        elif chart_type == "Scatter Plot (with OLS Trendline)":
            x_var = st.selectbox("Independent Variable (X-axis)", options=numeric_cols if numeric_cols else survey_cols, index=0)
            y_var = st.selectbox("Dependent Variable (Y-axis)", options=numeric_cols if numeric_cols else survey_cols, index=min(1, len(numeric_cols)-1))
            color_var = st.selectbox("Color Legend (Optional)", options=["None"] + survey_cols)
            add_trend = st.checkbox("Add OLS Linear Regression Fit Line", value=True)
        elif chart_type == "Correlation Heatmap Matrix":
            corr_vars = st.multiselect(
                "Select Variables for Heatmap",
                options=numeric_cols,
                default=numeric_cols[:6] if len(numeric_cols) >= 6 else numeric_cols
            )

    with col_ctrl2:
        st.markdown("#### 👁️ Interactive Chart Canvas")

        fig = None
        if chart_type == "Bar Chart (Frequencies & %)":
            fig = VisualizationEngine.bar_chart(df, chosen_var, title=chart_title or None)
        elif chart_type == "Pie / Donut Chart":
            fig = VisualizationEngine.pie_chart(df, chosen_var, title=chart_title or None)
        elif chart_type == "Histogram (Spread & Density)":
            fig = VisualizationEngine.histogram(df, chosen_var, bins=bins, title=chart_title or None)
        elif chart_type == "Box & Whisker Plot":
            x_val = None if x_var == "None" else x_var
            fig = VisualizationEngine.box_plot(df, y_col=y_var, x_col=x_val, title=chart_title or None)
        elif chart_type == "Scatter Plot (with OLS Trendline)":
            c_val = None if color_var == "None" else color_var
            fig = VisualizationEngine.scatter_plot(df, x_col=x_var, y_col=y_var, color_col=c_val, title=chart_title or None, add_trendline=add_trend)
        elif chart_type == "Correlation Heatmap Matrix":
            if len(corr_vars) >= 2:
                sub_corr = df[corr_vars].apply(pd.to_numeric, errors="coerce").corr().round(3)
                fig = VisualizationEngine.correlation_heatmap(sub_corr, title=chart_title or None)
            else:
                st.warning("Please select at least 2 variables to render correlation heatmap.")

        if fig:
            st.plotly_chart(fig, use_container_width=True)

