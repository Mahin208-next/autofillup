"""
Dashboard Page for SurveyForge AI.
Displays real-time platform statistics, interactive charts, and quick workflow actions.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from database.services import ProjectService
from database.db import SessionLocal
from database.models import Project, Question, SyntheticDataset, ValidationReport, ResearchVariable
from utils.formatting import render_metric_card
from core.visualization_engine import VisualizationEngine


def render():
    st.markdown("<div class='section-header'><h2>📊 Research Overview & Operations Dashboard</h2><p>Real-time dataset health, questionnaire metrics, and simulation controls.</p></div>", unsafe_allow_html=True)

    metrics = ProjectService.get_dashboard_metrics()
    project_id = st.session_state.get("current_project_id")

    # Fetch active project info
    db = SessionLocal()
    try:
        active_proj = db.query(Project).filter(Project.id == project_id).first()
        proj_name = active_proj.name if active_proj else "Default Project"
        proj_title = active_proj.title if active_proj else ""
        target_n = active_proj.target_sample_size if active_proj else 500

        # Project questions
        questions = db.query(Question).join(Question.questionnaire).filter(Question.questionnaire.has(project_id=project_id)).all()
        q_count = len(questions)

        # Datasets
        datasets = db.query(SyntheticDataset).filter(SyntheticDataset.project_id == project_id).all()
        ds_count = len(datasets)
        total_records_proj = sum(d.record_count for d in datasets)

        # Variables
        variables = db.query(ResearchVariable).filter(ResearchVariable.project_id == project_id).all()
        var_count = len(variables)

        # Latest validation for active project's latest dataset
        latest_ds = db.query(SyntheticDataset).filter(SyntheticDataset.project_id == project_id).order_by(SyntheticDataset.id.desc()).first()
        latest_val = None
        if latest_ds:
            latest_val = db.query(ValidationReport).filter(ValidationReport.dataset_id == latest_ds.id).order_by(ValidationReport.id.desc()).first()
    finally:
        db.close()

    # Active Project Banner
    st.info(f"**Current Research Focus:** {proj_title} (Target: {target_n} respondents, Adults 18+ in Bangladesh)")

    # 4-Column Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Imported Questions", q_count, f"Across active project", "#0284c7")
    with c2:
        render_metric_card("Synthetic Records", total_records_proj, f"In {ds_count} active dataset(s)", "#10b981")
    with c3:
        render_metric_card("Research Variables", var_count, "Configured scales & indices", "#f59e0b")
    with c4:
        status_text = latest_val.status if latest_val else "Not Run"
        score_val = f"{latest_val.score:.1f}%" if latest_val else "N/A"
        color = "#10b981" if status_text == "PASS" else ("#f59e0b" if status_text == "WARNING" else "#ef4444")
        render_metric_card("Validation Status", status_text, f"Score: {score_val}", color)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Quick Workflow Actions
    st.markdown("#### ⚡ Quick Workflow Actions")
    qa1, qa2, qa3, qa4, qa5 = st.columns(5)
    with qa1:
        if st.button("📁 New Project", use_container_width=True):
            st.session_state.nav_page = "📁 Project Manager"
            st.rerun()
    with qa2:
        if st.button("📥 Import Form", use_container_width=True):
            st.session_state.nav_page = "📥 Questionnaire Importer"
            st.rerun()
    with qa3:
        if st.button("⚡ Generate Data", use_container_width=True):
            st.session_state.nav_page = "⚡ Synthetic Data Generator"
            st.rerun()
    with qa4:
        if st.button("📋 Open Dataset", use_container_width=True):
            st.session_state.nav_page = "📋 Dataset Manager"
            st.rerun()
    with qa5:
        if st.button("📈 Run Analysis", use_container_width=True):
            st.session_state.nav_page = "📈 Statistical Analysis Studio"
            st.rerun()

    st.markdown("---")

    # Interactive Visualizations from Latest Dataset
    st.markdown("#### 📊 Demographic & Response Distributions (Latest Dataset)")

    if latest_ds and Path(latest_ds.file_path).exists():
        try:
            df = pd.read_csv(latest_ds.file_path)

            col_a, col_b = st.columns(2)

            with col_a:
                # Find age column
                age_col = next((c for c in df.columns if "age" in c.lower() and "q1" not in c.lower()), None)
                if age_col:
                    fig_age = VisualizationEngine.bar_chart(df, age_col, title="Age Group Distribution")
                    st.plotly_chart(fig_age, use_container_width=True)
                else:
                    st.write("No demographic age column identified.")

            with col_b:
                # Find education or gender column
                edu_col = next((c for c in df.columns if "education" in c.lower()), None)
                if edu_col:
                    fig_edu = VisualizationEngine.pie_chart(df, edu_col, title="Education Distribution")
                    st.plotly_chart(fig_edu, use_container_width=True)
                else:
                    gender_col = next((c for c in df.columns if "gender" in c.lower()), None)
                    if gender_col:
                        fig_gen = VisualizationEngine.pie_chart(df, gender_col, title="Gender Distribution")
                        st.plotly_chart(fig_gen, use_container_width=True)

            # Response distribution for key variable
            st.markdown("##### Key Likert Items Distribution")
            likert_cols = [c for c in df.columns if ("trust" in c.lower() or "risk" in c.lower()) and "comp_" not in c.lower()]
            if likert_cols:
                chosen_var = st.selectbox("Select Item to Inspect", options=likert_cols[:6])
                fig_hist = VisualizationEngine.histogram(df, chosen_var, bins=5, title=f"Frequency Breakdown: {chosen_var}")
                st.plotly_chart(fig_hist, use_container_width=True)

        except Exception as e:
            st.warning(f"Could not load charts from dataset file: {e}")
    else:
        st.info("No generated datasets found. Click 'Generate Synthetic Data' above to create your first sample.")

    st.markdown("---")

    # Recent generation history
    st.markdown("#### 🕒 Dataset Generation History")
    if metrics["recent_datasets"]:
        history_df = pd.DataFrame(metrics["recent_datasets"])
        history_df.columns = ["Dataset ID", "Name", "Sample Size (N)", "Seed", "Generated Date"]
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.write("No dataset generation events logged yet.")

