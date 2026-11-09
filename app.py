"""
SurveyForge AI — Main Application Entry Point
AI-Powered Synthetic Survey Data Generation & Statistical Analysis Platform
"""
import streamlit as st
from config import APP_NAME, APP_SUBTITLE, APP_VERSION
from utils.formatting import apply_custom_css, render_ethical_banner
from database.services import ProjectService
from database.db import SessionLocal
from database.models import Project

# Set up page config
st.set_page_config(
    page_title=f"{APP_NAME} — Survey Simulation Platform",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styling
apply_custom_css()

# Ensure database and default project exist
ProjectService.ensure_initialized()


def main():
    # Load available projects for sidebar switcher
    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id.asc()).all()
        project_options = {p.id: p.name for p in projects}
    finally:
        db.close()

    if not project_options:
        st.error("No active projects found. Please re-initialize database.")
        return

    # Initialize session state
    if "current_project_id" not in st.session_state:
        st.session_state.current_project_id = list(project_options.keys())[0]

    # Sidebar Navigation & Branding
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0; border-bottom: 1px solid #1e293b; margin-bottom: 1rem;">
                <h2 style="color: #38bdf8; margin: 0; font-size: 1.4rem; display: flex; align-items: center; gap: 0.5rem;">
                    🔬 {APP_NAME}
                </h2>
                <div style="color: #94a3b8; font-size: 0.78rem; margin-top: 0.2rem;">
                    {APP_SUBTITLE}
                </div>
                <div style="color: #64748b; font-size: 0.72rem; margin-top: 0.2rem;">
                    v{APP_VERSION} • Production Grade
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<p style='font-size: 0.8rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.2rem;'>ACTIVE RESEARCH PROJECT</p>", unsafe_allow_html=True)

        selected_id = st.selectbox(
            "Select Project",
            options=list(project_options.keys()),
            format_func=lambda x: f"📁 {project_options[x]}",
            index=list(project_options.keys()).index(st.session_state.current_project_id) if st.session_state.current_project_id in project_options else 0,
            label_visibility="collapsed"
        )
        st.session_state.current_project_id = selected_id

        st.markdown("---")
        st.markdown("<p style='font-size: 0.8rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.4rem;'>PLATFORM MODULES</p>", unsafe_allow_html=True)

        nav_options = [
            "📊 Dashboard",
            "📁 Project Manager",
            "📥 Questionnaire Importer",
            "🗂️ Question & Variable Manager",
            "👥 Respondent Profiles",
            "⚡ Synthetic Data Generator",
            "📋 Dataset Manager",
            "🛡️ Data Validation Engine",
            "📈 Statistical Analysis Studio",
            "📉 Visualization Studio",
            "📤 Export Center",
            "⚙️ Settings & System"
        ]

        if "nav_page" not in st.session_state:
            st.session_state.nav_page = nav_options[0]

        chosen_page = st.radio(
            "Navigate",
            options=nav_options,
            index=nav_options.index(st.session_state.nav_page) if st.session_state.nav_page in nav_options else 0,
            label_visibility="collapsed"
        )
        st.session_state.nav_page = chosen_page

        st.markdown("---")
        # Ethical tag indicator
        st.markdown(
            """
            <div style="background: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 6px; padding: 0.6rem; font-size: 0.75rem; color: #bae6fd;">
                <strong>PROVENANCE LOCK:</strong><br/>
                All outputs tagged <code>data_type = "synthetic"</code>.<br/>
                No submission to Google Forms.
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render Ethical Banner on every screen
    render_ethical_banner()

    # Dispatch to pages
    curr = st.session_state.nav_page
    if "Dashboard" in curr:
        from pages import dashboard
        dashboard.render()
    elif "Project Manager" in curr:
        from pages import projects
        projects.render()
    elif "Questionnaire Importer" in curr:
        from pages import questionnaire
        questionnaire.render()
    elif "Question & Variable Manager" in curr:
        from pages import question_manager
        question_manager.render()
    elif "Respondent Profiles" in curr:
        from pages import profiles
        profiles.render()
    elif "Synthetic Data Generator" in curr:
        from pages import generator
        generator.render()
    elif "Dataset Manager" in curr:
        from pages import dataset_manager
        dataset_manager.render()
    elif "Data Validation Engine" in curr:
        from pages import validation
        validation.render()
    elif "Statistical Analysis Studio" in curr:
        from pages import analysis
        analysis.render()
    elif "Visualization Studio" in curr:
        from pages import visualization
        visualization.render()
    elif "Export Center" in curr:
        from pages import exports
        exports.render()
    elif "Settings" in curr:
        from pages import settings
        settings.render()


if __name__ == "__main__":
    main()

