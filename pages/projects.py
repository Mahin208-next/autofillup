"""
Project Management Page for SurveyForge AI.
Enables creating, configuring, switching, and deleting academic research projects.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from database.db import SessionLocal
from database.models import Project, Questionnaire, Question, SyntheticDataset, ResearchVariable


def render():
    st.markdown("<div class='section-header'><h2>📁 Research Project Manager</h2><p>Organize, configure, and manage academic survey simulation projects.</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📚 All Projects", "➕ Create New Project", "⚙️ Edit Active Project"])

    db = SessionLocal()
    try:
        active_id = st.session_state.get("current_project_id")

        with tab1:
            projects = db.query(Project).order_by(Project.id.asc()).all()

            st.markdown("#### Registered Research Projects")
            p_data = []
            for p in projects:
                q_count = db.query(Question).join(Question.questionnaire).filter(Question.questionnaire.has(project_id=p.id)).count()
                d_count = db.query(SyntheticDataset).filter(SyntheticDataset.project_id == p.id).count()
                p_data.append({
                    "ID": p.id,
                    "Active": "⭐ CURRENT" if p.id == active_id else "",
                    "Project Name": p.name,
                    "Target N": p.target_sample_size,
                    "Target Population": p.target_population,
                    "Questions": q_count,
                    "Datasets": d_count,
                    "Created": p.created_at.strftime("%Y-%m-%d")
                })

            df_p = pd.DataFrame(p_data)
            st.dataframe(df_p, use_container_width=True, hide_index=True)

            col_sw1, col_sw2 = st.columns([3, 1])
            with col_sw1:
                switch_id = st.selectbox(
                    "Switch Active Workspace Project",
                    options=[p.id for p in projects],
                    format_func=lambda x: f"Project #{x}: {[p.name for p in projects if p.id == x][0]}"
                )
            with col_sw2:
                st.write("")
                st.write("")
                if st.button("Set as Active Project", use_container_width=True):
                    st.session_state.current_project_id = switch_id
                    st.success(f"Switched active project to #{switch_id}!")
                    st.rerun()

        with tab2:
            st.markdown("#### Create a New Research Project")
            with st.form("create_project_form"):
                p_name = st.text_input("Project Short Identifier / Name", placeholder="e.g., Maternal Telehealth Survey 2026")
                p_title = st.text_area(
                    "Full Academic Research Title",
                    placeholder="e.g., Evaluating Perceived Utility and Trust in Mobile Telehealth Services among Rural Populations in Bangladesh"
                )
                p_desc = st.text_area("Research Description / Objectives", placeholder="Outline the survey scope, hypotheses, and variables.")
                col_n, col_pop = st.columns(2)
                with col_n:
                    p_sample = st.number_input("Target Synthetic Sample Size (N)", min_value=10, max_value=50000, value=500, step=50)
                with col_pop:
                    p_pop = st.text_input("Target Population", value="Adults aged 18 or above in Bangladesh.")

                submitted = st.form_submit_button("Create Project", use_container_width=True)
                if submitted:
                    if not p_name.strip() or not p_title.strip():
                        st.error("Project name and academic research title are required.")
                    else:
                        new_proj = Project(
                            name=p_name.strip(),
                            title=p_title.strip(),
                            description=p_desc.strip(),
                            target_sample_size=int(p_sample),
                            target_population=p_pop.strip()
                        )
                        db.add(new_proj)
                        db.commit()
                        db.refresh(new_proj)
                        st.session_state.current_project_id = new_proj.id
                        st.success(f"Project '{new_proj.name}' created successfully and set as active workspace!")
                        st.rerun()

        with tab3:
            curr_proj = db.query(Project).filter(Project.id == active_id).first()
            if curr_proj:
                st.markdown(f"#### Edit Project #{curr_proj.id}: {curr_proj.name}")
                with st.form("edit_project_form"):
                    ed_name = st.text_input("Project Name", value=curr_proj.name)
                    ed_title = st.text_area("Academic Research Title", value=curr_proj.title)
                    ed_desc = st.text_area("Description", value=curr_proj.description or "")
                    c_n, c_pop = st.columns(2)
                    with c_n:
                        ed_sample = st.number_input("Target Sample Size (N)", value=curr_proj.target_sample_size)
                    with c_pop:
                        ed_pop = st.text_input("Target Population", value=curr_proj.target_population)

                    update_btn = st.form_submit_button("Save Changes", use_container_width=True)
                    if update_btn:
                        curr_proj.name = ed_name.strip()
                        curr_proj.title = ed_title.strip()
                        curr_proj.description = ed_desc.strip()
                        curr_proj.target_sample_size = int(ed_sample)
                        curr_proj.target_population = ed_pop.strip()
                        curr_proj.updated_at = datetime.now(timezone.utc)
                        db.commit()
                        st.success("Project updated successfully!")
                        st.rerun()

                st.markdown("---")
                st.markdown("##### ⚠️ Danger Zone")
                if not curr_proj.is_default:
                    if st.button("🗑️ Delete Current Project", type="secondary"):
                        db.delete(curr_proj)
                        db.commit()
                        st.session_state.current_project_id = 1
                        st.warning("Project deleted. Switched back to default project.")
                        st.rerun()
                else:
                    st.caption("The baseline demonstration project is protected and cannot be deleted.")

    finally:
        db.close()
