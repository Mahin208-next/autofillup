"""
Questionnaire Importer Page for SurveyForge AI.
Supports Google Forms public URLs, CSV, Excel, JSON, and Manual Questionnaire Builder.
"""
import streamlit as st
import json
import pandas as pd
from database.db import SessionLocal
from database.models import Project, Questionnaire, Question
from core.form_parser import FormParser
from config import DEFAULT_FORM_URL


def render():
    st.markdown("<div class='section-header'><h2>📥 Questionnaire Importer & Builder</h2><p>Extract questions dynamically from Google Forms, upload tabular instruments, or build questions manually.</p></div>", unsafe_allow_html=True)

    project_id = st.session_state.get("current_project_id")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔗 Google Forms URL",
        "📄 CSV File Upload",
        "📊 Excel (.xlsx) Upload",
        "📦 JSON Schema",
        "✍️ Manual Question Builder"
    ])

    # TAB 1: Google Forms
    with tab1:
        st.markdown("#### Dynamic Google Forms Extraction")
        st.write("Enter the public shareable link of a Google Form. SurveyForge AI inspects the schema, extracts all question titles, answer options, scales, and required statuses.")

        g_url = st.text_input("Google Forms Public URL", value=DEFAULT_FORM_URL)

        col_g1, col_g2 = st.columns([2, 1])
        with col_g1:
            fetch_btn = st.button("🔍 Extract Questionnaire Structure", use_container_width=True)

        if fetch_btn:
            with st.spinner("Extracting public questionnaire metadata..."):
                res = FormParser.parse_google_form(g_url)

            if res["success"]:
                st.success(f"Successfully parsed questionnaire: **{res.get('title')}** ({len(res['questions'])} questions extracted)")
                if res.get("is_cached"):
                    st.info(f"ℹ️ {res.get('notice')}")

                st.session_state.temp_extracted_questions = res["questions"]
                st.session_state.temp_extracted_title = res.get("title", "Google Form Questionnaire")
                st.session_state.temp_source_type = "google_forms"
                st.session_state.temp_source_url = g_url
            else:
                st.error(res["error"])

        # Display preview if extracted
        if "temp_extracted_questions" in st.session_state and st.session_state.temp_source_type == "google_forms":
            _render_extracted_preview(project_id)

    # TAB 2: CSV
    with tab2:
        st.markdown("#### Import Questionnaire from CSV")
        st.write("Upload a CSV file containing columns: `question_text`, `question_type`, `options`, `category`, `required`.")

        template_csv_path = Path("assets/sample_questionnaire_template.csv")
        if template_csv_path.exists():
            with open(template_csv_path, "rb") as f:
                st.download_button(
                    "📥 Download Sample CSV Questionnaire Template",
                    data=f.read(),
                    file_name="SurveyForge_Questionnaire_Template.csv",
                    mime="text/csv",
                    help="Use this template to format questions for upload"
                )

        csv_file = st.file_uploader("Upload CSV Questionnaire", type=["csv"], key="csv_uploader")
        if csv_file:
            res = FormParser.parse_csv(csv_file)
            if res["success"]:
                st.success(f"Parsed {len(res['questions'])} questions from CSV.")
                st.session_state.temp_extracted_questions = res["questions"]
                st.session_state.temp_extracted_title = csv_file.name
                st.session_state.temp_source_type = "csv"
                st.session_state.temp_source_url = csv_file.name
                _render_extracted_preview(project_id)
            else:
                st.error(res["error"])

    # TAB 3: Excel
    with tab3:
        st.markdown("#### Import Questionnaire from Excel")
        st.write("Upload an Excel file (.xlsx) with questionnaire columns.")

        template_xlsx_path = Path("assets/sample_questionnaire_template.xlsx")
        if template_xlsx_path.exists():
            with open(template_xlsx_path, "rb") as f:
                st.download_button(
                    "📥 Download Sample Excel Questionnaire Template",
                    data=f.read(),
                    file_name="SurveyForge_Questionnaire_Template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Use this template to format questions in Excel"
                )

        excel_file = st.file_uploader("Upload Excel Questionnaire", type=["xlsx", "xls"], key="excel_uploader")
        if excel_file:
            res = FormParser.parse_excel(excel_file)
            if res["success"]:
                st.success(f"Parsed {len(res['questions'])} questions from Excel.")
                st.session_state.temp_extracted_questions = res["questions"]
                st.session_state.temp_extracted_title = excel_file.name
                st.session_state.temp_source_type = "excel"
                st.session_state.temp_source_url = excel_file.name
                _render_extracted_preview(project_id)
            else:
                st.error(res["error"])

    # TAB 4: JSON
    with tab4:
        st.markdown("#### Import Questionnaire from JSON")
        json_input = st.text_area("Paste JSON Question Array", height=200, placeholder='[\n  {\n    "question_id": "Q1",\n    "question_text": "Sample question?",\n    "question_type": "Likert Scale",\n    "answer_options": ["1 - Strongly Disagree", "5 - Strongly Agree"]\n  }\n]')
        if st.button("Parse JSON Questions"):
            res = FormParser.parse_json(json_input)
            if res["success"]:
                st.success(f"Parsed {len(res['questions'])} questions from JSON.")
                st.session_state.temp_extracted_questions = res["questions"]
                st.session_state.temp_extracted_title = "JSON Questionnaire"
                st.session_state.temp_source_type = "json"
                st.session_state.temp_source_url = "Manual JSON"
                _render_extracted_preview(project_id)
            else:
                st.error(res["error"])

    # TAB 5: Manual Question Builder
    with tab5:
        st.markdown("#### ✍️ Add Question Manually to Active Questionnaire")
        with st.form("manual_add_question_form"):
            q_id = st.text_input("Question ID (e.g. Q43, TRUST_01)", value="Q_NEW")
            q_text = st.text_area("Question Text", placeholder="e.g., I find medical advice generated by AI chatbots to be accurate and reliable.")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                q_type = st.selectbox(
                    "Question Type",
                    options=[
                        "Likert Scale",
                        "Multiple Choice",
                        "Checkboxes",
                        "Short Answer",
                        "Paragraph",
                        "Dropdown",
                        "Linear Scale",
                        "Yes/No",
                        "Numeric",
                        "Date"
                    ]
                )
            with col_t2:
                q_cat = st.selectbox(
                    "Category",
                    options=[
                        "Demographics",
                        "AI Chatbot Usage",
                        "Social Media Usage",
                        "Trust in AI Chatbots",
                        "Trust in Social Media",
                        "Perceived Risk",
                        "Digital Health Literacy",
                        "Information Verification",
                        "Healthcare Access",
                        "Self-Medication Behavior",
                        "General"
                    ]
                )

            q_opts_str = st.text_area(
                "Answer Options (one per line or comma-separated)",
                value="1 - Strongly Disagree\n2 - Disagree\n3 - Neutral\n4 - Agree\n5 - Strongly Agree" if q_type == "Likert Scale" else ""
            )

            col_chk1, col_chk2 = st.columns(2)
            with col_chk1:
                q_req = st.checkbox("Required Question", value=True)
            with col_chk2:
                q_rev = st.checkbox("Reverse Coded Item", value=False)

            add_btn = st.form_submit_button("Add Question to Active Project", use_container_width=True)
            if add_btn:
                if not q_text.strip():
                    st.error("Question text cannot be empty.")
                else:
                    opts = [line.strip() for line in q_opts_str.split("\n") if line.strip()]
                    if not opts and "," in q_opts_str:
                        opts = [o.strip() for o in q_opts_str.split(",") if o.strip()]

                    _save_manual_question(project_id, q_id, q_text, q_type, q_cat, opts, q_req, q_rev)


def _render_extracted_preview(project_id: int):
    """Renders table of extracted questions with confirmation button to save to DB."""
    questions = st.session_state.get("temp_extracted_questions", [])
    title = st.session_state.get("temp_extracted_title", "Imported Questionnaire")
    st.markdown("---")
    st.markdown(f"#### Review Extracted Questionnaire ({len(questions)} items)")

    preview_rows = []
    for q in questions:
        preview_rows.append({
            "ID": q.get("question_id"),
            "Question Text": q.get("question_text")[:80] + ("..." if len(q.get("question_text", "")) > 80 else ""),
            "Type": q.get("question_type"),
            "Category": q.get("category"),
            "Required": "Yes" if q.get("required") else "No",
            "Options Count": len(q.get("answer_options", []))
        })

    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        if st.button("💾 Save Questionnaire to Active Project", type="primary", use_container_width=True):
            _save_imported_questionnaire(project_id, title, questions)


def _save_imported_questionnaire(project_id: int, title: str, questions: list):
    """Persist imported questions into active project questionnaire."""
    db = SessionLocal()
    try:
        # Check if project already has a questionnaire
        existing_q = db.query(Questionnaire).filter(Questionnaire.project_id == project_id).first()
        if existing_q:
            # Overwrite or update
            existing_q.title = title
            existing_q.source_type = st.session_state.get("temp_source_type", "import")
            existing_q.source_url_or_path = st.session_state.get("temp_source_url", "")
            # Delete old questions
            db.query(Question).filter(Question.questionnaire_id == existing_q.id).delete()
            q_id = existing_q.id
        else:
            new_q = Questionnaire(
                project_id=project_id,
                title=title,
                source_type=st.session_state.get("temp_source_type", "import"),
                source_url_or_path=st.session_state.get("temp_source_url", "")
            )
            db.add(new_q)
            db.commit()
            db.refresh(new_q)
            q_id = new_q.id

        # Insert questions
        for idx, item in enumerate(questions):
            q_obj = Question(
                questionnaire_id=q_id,
                question_id=item.get("question_id") or f"Q{idx+1}",
                question_text=item.get("question_text"),
                question_type=item.get("question_type", "Multiple Choice"),
                answer_options=json.dumps(item.get("answer_options", []), ensure_ascii=False),
                required=item.get("required", True),
                variable_name=item.get("variable_name") or f"q{idx+1}",
                category=item.get("category", "General"),
                reverse_coded=item.get("reverse_coded", False),
                validation_rules=json.dumps(item.get("validation_rules", {})),
                order_num=idx + 1
            )
            db.add(q_obj)
        db.commit()
        st.success(f"Saved {len(questions)} questions to project questionnaire!")
        del st.session_state["temp_extracted_questions"]
        st.rerun()
    finally:
        db.close()


def _save_manual_question(project_id: int, qid: str, text: str, qtype: str, cat: str, opts: list, req: bool, rev: bool):
    """Save single manually built question."""
    db = SessionLocal()
    try:
        q_parent = db.query(Questionnaire).filter(Questionnaire.project_id == project_id).first()
        if not q_parent:
            q_parent = Questionnaire(project_id=project_id, title="Project Survey Instrument", source_type="manual")
            db.add(q_parent)
            db.commit()
            db.refresh(q_parent)

        max_order = db.query(Question).filter(Question.questionnaire_id == q_parent.id).count()
        var_name = f"{qid.lower()}_{cat.lower()[:10]}"

        new_q = Question(
            questionnaire_id=q_parent.id,
            question_id=qid.strip(),
            question_text=text.strip(),
            question_type=qtype,
            answer_options=json.dumps(opts, ensure_ascii=False),
            required=req,
            variable_name=var_name,
            category=cat,
            reverse_coded=rev,
            order_num=max_order + 1
        )
        db.add(new_q)
        db.commit()
        st.success(f"Question '{qid}' added successfully to active survey instrument!")
        st.rerun()
    finally:
        db.close()

