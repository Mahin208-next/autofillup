"""
Question Classification & Research Variable Mapping Page for SurveyForge AI.
Allows editing questionnaire items, categorizing, reverse-coding, and building composite latent constructs.
"""
import streamlit as st
import json
import pandas as pd
from database.db import SessionLocal
from database.models import Project, Questionnaire, Question, ResearchVariable
from core.question_mapper import QuestionMapper


def render():
    st.markdown("<div class='section-header'><h2>🗂️ Question Classification & Variable Mapping</h2><p>Classify survey items, assign reverse coding, and group items into theoretical research variables.</p></div>", unsafe_allow_html=True)

    project_id = st.session_state.get("current_project_id")

    tab_items, tab_vars, tab_codebook, tab_edit = st.tabs([
        "📋 Questionnaire Items & Categories",
        "🎯 Research Variables & Composite Scales",
        "📖 Survey Codebook",
        "✏️ Edit Individual Question"
    ])

    db = SessionLocal()
    try:
        # Load questions
        q_objs = (
            db.query(Question)
            .join(Question.questionnaire)
            .filter(Question.questionnaire.has(project_id=project_id))
            .order_by(Question.order_num.asc())
            .all()
        )

        # TAB 1: Questionnaire Items & Categories
        with tab_items:
            st.markdown(f"#### Active Questionnaire Items ({len(q_objs)} items)")
            if not q_objs:
                st.info("No questions in active project. Please use Questionnaire Importer to add items.")
            else:
                # Category Filter
                all_cats = sorted(list(set(q.category for q in q_objs if q.category)))
                selected_cat = st.selectbox("Filter by Category", options=["All Categories"] + all_cats)

                filtered_q = q_objs if selected_cat == "All Categories" else [q for q in q_objs if q.category == selected_cat]

                table_data = []
                for q in filtered_q:
                    table_data.append({
                        "ID": q.question_id,
                        "Variable Name": q.variable_name,
                        "Category": q.category,
                        "Type": q.question_type,
                        "Required": "Yes" if q.required else "No",
                        "Reverse Coded": "⚠️ Yes" if q.reverse_coded else "No",
                        "Question Text": q.question_text[:100] + ("..." if len(q.question_text) > 100 else "")
                    })

                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        # TAB 2: Research Variables & Composite Scales
        with tab_vars:
            st.markdown("#### Research Variables (Theoretical Constructs)")
            st.write("Group multiple questionnaire Likert items under unified research variables (Independent, Dependent, Control).")

            r_vars = db.query(ResearchVariable).filter(ResearchVariable.project_id == project_id).all()

            if r_vars:
                var_rows = []
                for rv in r_vars:
                    qids = rv.get_question_ids()
                    var_rows.append({
                        "ID": rv.id,
                        "Construct Name": rv.name,
                        "Type": rv.variable_type.upper(),
                        "Grouped Items": ", ".join(qids),
                        "Composite Calculation": rv.composite_method.upper(),
                        "Description": rv.description
                    })
                st.dataframe(pd.DataFrame(var_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No research variables mapped yet. Define one below.")

            st.markdown("---")
            st.markdown("##### ➕ Define / Map New Research Variable")
            with st.form("add_research_var_form"):
                v_name = st.text_input("Variable Name", placeholder="e.g., Perceived Risk of AI Medical Advice")
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    v_type = st.selectbox("Role in Research Model", options=["independent", "dependent", "control", "demographic"])
                with col_v2:
                    v_method = st.selectbox("Composite Score Method", options=["mean", "sum"])

                v_desc = st.text_input("Theoretical Definition / Construct Scope", placeholder="Explains the underlying psychological or behavioral concept.")

                # Multi-select questionnaire items
                available_qids = [f"{q.question_id} ({q.variable_name})" for q in q_objs]
                chosen_q_labels = st.multiselect("Select Questionnaire Items to Group", options=available_qids)

                save_var_btn = st.form_submit_button("Save Research Variable", use_container_width=True)
                if save_var_btn:
                    if not v_name.strip():
                        st.error("Variable name is required.")
                    elif not chosen_q_labels:
                        st.error("Please select at least one question item to map.")
                    else:
                        clean_qids = [label.split(" ")[0] for label in chosen_q_labels]
                        new_rv = ResearchVariable(
                            project_id=project_id,
                            name=v_name.strip(),
                            variable_type=v_type,
                            description=v_desc.strip(),
                            composite_method=v_method
                        )
                        new_rv.set_question_ids(clean_qids)
                        db.add(new_rv)
                        db.commit()
                        st.success(f"Variable '{v_name}' successfully mapped!")
                        st.rerun()

            # Variable Deletion
            if r_vars:
                st.markdown("##### 🗑️ Remove Research Variable")
                del_id = st.selectbox("Select Variable to Delete", options=[rv.id for rv in r_vars], format_func=lambda x: [rv.name for rv in r_vars if rv.id == x][0])
                if st.button("Delete Selected Variable"):
                    target = db.query(ResearchVariable).filter(ResearchVariable.id == del_id).first()
                    if target:
                        db.delete(target)
                        db.commit()
                        st.success("Variable deleted.")
                        st.rerun()

        # TAB 3: Research Codebook
        with tab_codebook:
            st.markdown("#### Academic Survey Codebook")
            st.write("Formal measurement metadata, question definitions, and scale specifications.")

            if not q_objs:
                st.info("No questions in active questionnaire.")
            else:
                codebook_rows = []
                for q in q_objs:
                    # Infer measurement level
                    if q.question_type == "Likert Scale" or q.question_type == "Linear Scale":
                        meas_level = "Ordinal / Interval"
                    elif q.question_type in ("Numeric"):
                        meas_level = "Scale / Ratio"
                    elif q.question_type in ("Multiple Choice", "Dropdown", "Checkboxes", "Yes/No"):
                        meas_level = "Nominal"
                    else:
                        meas_level = "Textual / String"

                    codebook_rows.append({
                        "Variable Name": q.variable_name,
                        "Item ID": q.question_id,
                        "Category": q.category,
                        "Measurement Level": meas_level,
                        "Type": q.question_type,
                        "Required": "Yes" if q.required else "No",
                        "Reverse Coded": "Yes" if q.reverse_coded else "No",
                        "Answer Options": ", ".join(q.get_options()) if q.get_options() else "N/A",
                        "Question Text": q.question_text
                    })

                cb_df = pd.DataFrame(codebook_rows)
                st.dataframe(cb_df, use_container_width=True, hide_index=True)

                csv_cb = cb_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Codebook (CSV)",
                    data=csv_cb,
                    file_name="Survey_Codebook.csv",
                    mime="text/csv"
                )

        # TAB 4: Edit Individual Question
        with tab_edit:
            st.markdown("#### Edit Questionnaire Item Attributes")
            if not q_objs:
                st.write("No questions available.")
            else:
                edit_qid = st.selectbox(
                    "Select Question to Edit",
                    options=[q.id for q in q_objs],
                    format_func=lambda x: f"{[q.question_id for q in q_objs if q.id == x][0]} — {[q.question_text[:60] for q in q_objs if q.id == x][0]}"
                )

                selected_q = db.query(Question).filter(Question.id == edit_qid).first()
                if selected_q:
                    with st.form("edit_single_q_form"):
                        e_text = st.text_area("Question Text", value=selected_q.question_text)
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            e_type = st.selectbox(
                                "Question Type",
                                options=["Likert Scale", "Multiple Choice", "Checkboxes", "Short Answer", "Paragraph", "Dropdown", "Linear Scale", "Yes/No", "Numeric", "Date"],
                                index=["Likert Scale", "Multiple Choice", "Checkboxes", "Short Answer", "Paragraph", "Dropdown", "Linear Scale", "Yes/No", "Numeric", "Date"].index(selected_q.question_type) if selected_q.question_type in ["Likert Scale", "Multiple Choice", "Checkboxes", "Short Answer", "Paragraph", "Dropdown", "Linear Scale", "Yes/No", "Numeric", "Date"] else 0
                            )
                        with col_e2:
                            e_cat = st.text_input("Category", value=selected_q.category)

                        e_var = st.text_input("Clean Variable Name (Column Name in Dataset)", value=selected_q.variable_name)

                        opts_list = selected_q.get_options()
                        e_opts_str = st.text_area("Options (one per line)", value="\n".join(opts_list))

                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            e_req = st.checkbox("Required Field", value=selected_q.required)
                        with col_c2:
                            e_rev = st.checkbox("Reverse Coded Item (Negative Phrasing)", value=selected_q.reverse_coded)

                        save_q_btn = st.form_submit_button("Update Question", use_container_width=True)
                        if save_q_btn:
                            selected_q.question_text = e_text.strip()
                            selected_q.question_type = e_type
                            selected_q.category = e_cat.strip()
                            selected_q.variable_name = e_var.strip()
                            new_opts = [line.strip() for line in e_opts_str.split("\n") if line.strip()]
                            selected_q.set_options(new_opts)
                            selected_q.required = e_req
                            selected_q.reverse_coded = e_rev
                            db.commit()
                            st.success(f"Question {selected_q.question_id} updated!")
                            st.rerun()

                    if st.button("🗑️ Delete this Question", key="del_q_btn"):
                        db.delete(selected_q)
                        db.commit()
                        st.warning("Question deleted.")
                        st.rerun()

    finally:
        db.close()

