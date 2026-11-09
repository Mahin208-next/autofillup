"""
Data Validation Engine Page for SurveyForge AI.
Performs 9-point integrity audit on synthetic survey datasets and renders comprehensive quality reports.
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from database.db import SessionLocal
from database.models import Project, Question, SyntheticDataset, ValidationReport
from core.validation_engine import ValidationEngine
from utils.formatting import render_metric_card


def render():
    st.markdown("<div class='section-header'><h2>🛡️ Synthetic Survey Data Validation Engine</h2><p>Execute rigorous 9-point quality, skip-logic, and distributional integrity audits.</p></div>", unsafe_allow_html=True)

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
            st.info("No datasets found to validate. Please generate a synthetic dataset first.")
            return

        ds_map = {ds.id: f"#{ds.id} — {ds.name} (N={ds.record_count})" for ds in datasets}
        selected_ds_id = st.selectbox("Select Dataset to Audit", options=list(ds_map.keys()), format_func=lambda x: ds_map[x])

        target_ds = db.query(SyntheticDataset).filter(SyntheticDataset.id == selected_ds_id).first()
        val_report_obj = db.query(ValidationReport).filter(ValidationReport.dataset_id == selected_ds_id).order_by(ValidationReport.id.desc()).first()

        # Questions for validation schema
        q_objs = (
            db.query(Question)
            .join(Question.questionnaire)
            .filter(Question.questionnaire.has(project_id=project_id))
            .all()
        )
        questions_data = [
            {
                "question_id": q.question_id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "answer_options": q.get_options(),
                "required": q.required,
                "variable_name": q.variable_name,
                "category": q.category,
                "reverse_coded": q.reverse_coded,
                "validation_rules": json.loads(q.validation_rules) if q.validation_rules else {}
            }
            for q in q_objs
        ]

    finally:
        db.close()

    if not Path(target_ds.file_path).exists():
        st.error(f"Dataset file missing from disk: {target_ds.file_path}")
        return

    df = pd.read_csv(target_ds.file_path)

    # Re-run Audit button
    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
        st.markdown(f"#### Active Dataset: **{target_ds.name}** (N = {len(df)})")
    with col_hdr2:
        if st.button("🔄 Re-run Complete 9-Point Audit", type="primary", use_container_width=True):
            with st.spinner("Executing structural and semantic validation suite..."):
                val_res = ValidationEngine.validate_dataset(df, questions_data)

                # Persist to DB
                db = SessionLocal()
                try:
                    new_rep = ValidationReport(
                        dataset_id=target_ds.id,
                        status=val_res["status"],
                        score=val_res["score"],
                        summary_json=json.dumps(val_res["summary"]),
                        details_json=json.dumps(val_res["details"])
                    )
                    db.add(new_rep)
                    # Update dataset status
                    ds_record = db.query(SyntheticDataset).filter(SyntheticDataset.id == target_ds.id).first()
                    if ds_record:
                        ds_record.status = "validated" if val_res["status"] != "FAIL" else "failed"
                    db.commit()
                finally:
                    db.close()

            st.success(f"Audit completed: Status = {val_res['status']} ({val_res['score']}%)")
            st.rerun()

    # Load Report
    if val_report_obj:
        status = val_report_obj.status
        score = val_report_obj.score
        summary = json.loads(val_report_obj.summary_json) if val_report_obj.summary_json else {}
        details = json.loads(val_report_obj.details_json) if val_report_obj.details_json else []
    else:
        # Run validation right now if none exists
        val_res = ValidationEngine.validate_dataset(df, questions_data)
        status = val_res["status"]
        score = val_res["score"]
        summary = val_res["summary"]
        details = val_res["details"]

    # Status Cards
    st.markdown("<br/>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    stat_color = "#10b981" if status == "PASS" else ("#f59e0b" if status == "WARNING" else "#ef4444")
    with c1:
        render_metric_card("Overall Verdict", status, "Benchmark: PASS/WARNING", stat_color)
    with c2:
        render_metric_card("Quality Score", f"{score:.1f}%", "Out of 100.0%", "#0284c7")
    with c3:
        render_metric_card("Passed Checks", f"{summary.get('passed_checks', 0)} / 9", "Integrity criteria verified", "#10b981")
    with c4:
        render_metric_card("Missing Cell Rate", f"{summary.get('missing_cell_rate_pct', 0.0)}%", f"Duplicate rows: {summary.get('duplicate_rows', 0)}", "#64748b")

    st.markdown("---")

    # Audit Checklist
    st.markdown("#### 📋 9-Point Quality & Integrity Checklist")

    for item in details:
        chk_name = item.get("check")
        chk_stat = item.get("status")
        chk_msg = item.get("message")

        if chk_stat == "PASS":
            icon = "✅"
            badge_class = "badge-pass"
        elif chk_stat == "WARNING":
            icon = "⚠️"
            badge_class = "badge-warning"
        else:
            icon = "❌"
            badge_class = "badge-fail"

        st.markdown(
            f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.85rem 1.1rem; margin-bottom: 0.6rem; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.25rem;">{icon}</span>
                    <div>
                        <span style="font-weight: 600; font-size: 0.92rem; color: #0f172a;">{chk_name}</span>
                        <div style="color: #64748b; font-size: 0.82rem; margin-top: 0.15rem;">{chk_msg}</div>
                    </div>
                </div>
                <div>
                    <span class="badge {badge_class}">{chk_stat}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("##### 🔬 Missingness by Variable Breakdown")
    missing_by_col = df.isna().sum()
    missing_by_col = missing_by_col[missing_by_col > 0]
    if len(missing_by_col) > 0:
        miss_df = pd.DataFrame({
            "Variable": missing_by_col.index,
            "Missing Count": missing_by_col.values,
            "Missing Percentage": (missing_by_col.values / len(df) * 100).round(2)
        })
        st.dataframe(miss_df, use_container_width=True, hide_index=True)
    else:
        st.success("Zero missing cells across all variables in this dataset.")

