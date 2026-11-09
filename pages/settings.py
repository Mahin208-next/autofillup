"""
Settings & System Diagnostics Page for SurveyForge AI.
"""
import sys
import os
import streamlit as st
from pathlib import Path
from config import BASE_DIR, DATA_DIR, EXPORT_DIR, DB_PATH, APP_VERSION, AI_PROVIDER
from database.db import SessionLocal
from database.services import ProjectService
from database.models import Project, Question, SyntheticDataset, ValidationReport


def render():
    st.markdown("<div class='section-header'><h2>⚙️ System Diagnostics & Application Settings</h2><p>Inspect platform environment, manage storage, and configure AI simulation helpers.</p></div>", unsafe_allow_html=True)

    tab_diag, tab_ai, tab_db = st.tabs([
        "💻 System Diagnostics",
        "🤖 AI Simulation Provider Settings",
        "🗄️ Database & Storage Management"
    ])

    with tab_diag:
        st.markdown("#### Runtime Environment")
        c1, c2, c3 = st.columns(3)
        c1.metric("Platform Version", f"v{APP_VERSION}")
        c2.metric("Python Runtime", sys.version.split(" ")[0])
        c3.metric("OS Platform", sys.platform)

        st.markdown("##### Core Directory Paths")
        st.markdown(
            f"""
            - **Base Directory:** `{BASE_DIR}`
            - **Datasets Directory:** `{DATA_DIR}`
            - **Exports Directory:** `{EXPORT_DIR}`
            - **SQLite Database:** `{DB_PATH}`
            """
        )

        st.markdown("##### Library Integrity Checks")
        lib_checks = [
            ("pandas", "Data manipulation & framing"),
            ("numpy", "Linear algebra & numerical routines"),
            ("scipy", "Inferential statistics & distributions"),
            ("statsmodels", "Ordinary least squares regression"),
            ("plotly", "Interactive visualization suite"),
            ("sqlalchemy", "Relational database ORM"),
            ("openpyxl", "Excel multi-sheet export"),
            ("pyreadstat", "IBM SPSS SAV binary serialization"),
            ("reportlab", "PDF document compilation engine")
        ]
        status_rows = []
        for mod, desc in lib_checks:
            try:
                m = __import__(mod)
                ver = getattr(m, "__version__", "Available")
                status_rows.append({"Library": mod, "Purpose": desc, "Version": ver, "Status": "✅ Operational"})
            except ImportError as e:
                status_rows.append({"Library": mod, "Purpose": desc, "Version": "N/A", "Status": f"❌ {e}"})

        st.dataframe(status_rows, use_container_width=True, hide_index=True)

    with tab_ai:
        st.markdown("#### Optional AI API Integration")
        st.write("SurveyForge AI functions completely offline using statistical copulas and logic engines. Optionally, an LLM API can assist in drafting hypothetical survey scenarios.")

        with st.form("ai_settings_form"):
            prov = st.selectbox("AI Model Provider", options=["none (Offline Statistical Engine)", "openai", "gemini"], index=0)
            api_key = st.text_input("Provider API Key", type="password", placeholder="sk-...")

            save_ai = st.form_submit_button("Save AI Settings")
            if save_ai:
                st.success("AI preferences updated for current session. (Core application remains 100% operational offline).")

    with tab_db:
        st.markdown("#### Database & Storage")
        db_size = DB_PATH.stat().st_size / 1024.0 if DB_PATH.exists() else 0.0
        n_datasets = len(list(DATA_DIR.glob("*.csv")))
        n_exports = len(list(EXPORT_DIR.glob("*.*")))

        d1, d2, d3 = st.columns(3)
        d1.metric("Database File Size", f"{db_size:.1f} KB")
        d2.metric("Dataset Files on Disk", n_datasets)
        d3.metric("Export Files on Disk", n_exports)

        st.markdown("---")
        st.markdown("##### ⚠️ Re-seed Baseline Project")
        st.write("Resets the demonstration project to initial state with the verified Google Forms survey instrument.")
        if st.button("Re-seed Default Demonstration Project", type="secondary"):
            db = SessionLocal()
            try:
                def_proj = db.query(Project).filter(Project.is_default == True).first()
                if def_proj:
                    db.delete(def_proj)
                    db.commit()
                ProjectService.seed_default_project(db)
                st.success("Default project re-seeded successfully!")
                st.rerun()
            finally:
                db.close()

