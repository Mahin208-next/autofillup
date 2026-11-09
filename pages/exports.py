"""
Export Center Page for SurveyForge AI.
Handles CSV, multi-sheet Excel (.xlsx), SPSS (.sav), and PDF report downloads with provenance disclaimers.
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from database.db import SessionLocal
from database.models import (
    Project, SyntheticDataset, DatasetMetadata, ValidationReport,
    Question, AnalysisResult, ExportHistory
)
from core.export_engine import ExportEngine
from config import EXPORT_DIR, DEFAULT_DISCLAIMER


def render():
    st.markdown("<div class='section-header'><h2>📤 Export Center & Archival</h2><p>Export synthetic research datasets and publication-ready statistical reports with mandatory provenance tags.</p></div>", unsafe_allow_html=True)

    project_id = st.session_state.get("current_project_id")

    db = SessionLocal()
    try:
        active_proj = db.query(Project).filter(Project.id == project_id).first()
        datasets = (
            db.query(SyntheticDataset)
            .filter(SyntheticDataset.project_id == project_id)
            .order_by(SyntheticDataset.id.desc())
            .all()
        )

        q_objs = (
            db.query(Question)
            .join(Question.questionnaire)
            .filter(Question.questionnaire.has(project_id=project_id))
            .all()
        )
        questions_list = [
            {
                "question_id": q.question_id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "answer_options": q.get_options(),
                "required": q.required,
                "variable_name": q.variable_name,
                "category": q.category,
                "reverse_coded": q.reverse_coded
            }
            for q in q_objs
        ]

        analysis_items = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.project_id == project_id)
            .all()
        )
        analysis_data = [
            {
                "test_name": a.test_name,
                "sample_size": a.sample_size,
                "test_statistic": a.test_statistic,
                "p_value": a.p_value,
                "interpretation": a.interpretation
            }
            for a in analysis_items
        ]

        if not datasets:
            st.info("No datasets available to export. Please generate a synthetic dataset first.")
            return

        ds_map = {ds.id: f"#{ds.id} — {ds.name} (N={ds.record_count})" for ds in datasets}
        selected_ds_id = st.selectbox("Select Synthetic Dataset to Export", options=list(ds_map.keys()), format_func=lambda x: ds_map[x])

        target_ds = db.query(SyntheticDataset).filter(SyntheticDataset.id == selected_ds_id).first()
        metadata_obj = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == selected_ds_id).first()
        val_obj = db.query(ValidationReport).filter(ValidationReport.dataset_id == selected_ds_id).order_by(ValidationReport.id.desc()).first()

        exports_history = (
            db.query(ExportHistory)
            .filter(ExportHistory.project_id == project_id)
            .order_by(ExportHistory.id.desc())
            .all()
        )

    finally:
        db.close()

    if not Path(target_ds.file_path).exists():
        st.error(f"Dataset file missing from disk: {target_ds.file_path}")
        return

    df = pd.read_csv(target_ds.file_path)

    st.markdown(
        f"""
        <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 0.8rem 1.1rem; border-radius: 6px; font-size: 0.84rem; color: #991b1b; margin-bottom: 1.25rem;">
            <strong>MANDATORY SYNTHETIC DISCLAIMER EMBEDDED IN ALL EXPORTS:</strong><br/>
            "{DEFAULT_DISCLAIMER}"
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    # 1. CSV Export
    with col1:
        st.markdown(
            """
            <div class="forge-card">
                <h4>📄 CSV Dataset Export</h4>
                <p style="font-size: 0.82rem; color: #64748b;">Includes full synthetic records with top disclaimer comment block and provenance metadata.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        csv_bytes = ExportEngine.export_csv(df)
        csv_filename = f"SurveyForge_{target_ds.id}_seed{target_ds.random_seed}_synthetic.csv"

        if st.download_button(
            label="⬇️ Download Dataset (CSV)",
            data=csv_bytes,
            file_name=csv_filename,
            mime="text/csv",
            use_container_width=True
        ):
            _log_export(project_id, target_ds.id, "csv", str(EXPORT_DIR / csv_filename), len(df))

    # 2. Excel Multi-Sheet
    with col2:
        st.markdown(
            """
            <div class="forge-card">
                <h4>📊 Excel Multi-Sheet Workbook (.xlsx)</h4>
                <p style="font-size: 0.82rem; color: #64748b;">4 structured sheets: Synthetic Data, Metadata & Assumptions, Validation Summary, and Codebook.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        meta_dict = json.loads(metadata_obj.metadata_json) if metadata_obj and metadata_obj.metadata_json else {}
        val_summary = json.loads(val_obj.summary_json) if val_obj and val_obj.summary_json else {}

        excel_bytes = ExportEngine.export_excel(
            df=df,
            metadata=meta_dict,
            validation_summary=val_summary,
            questions=questions_list
        )
        excel_filename = f"SurveyForge_{target_ds.id}_synthetic_workbook.xlsx"

        if st.download_button(
            label="⬇️ Download Multi-Sheet Excel (.xlsx)",
            data=excel_bytes,
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        ):
            _log_export(project_id, target_ds.id, "excel", str(EXPORT_DIR / excel_filename), len(df))

    st.markdown("<br/>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)

    # 3. SPSS SAV
    with col3:
        st.markdown(
            """
            <div class="forge-card">
                <h4>💾 IBM SPSS Compatible File (.sav)</h4>
                <p style="font-size: 0.82rem; color: #64748b;">Directly imports into SPSS 28/29 with truncated variable tags and synthetic file labels.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        spss_filename = f"SurveyForge_{target_ds.id}_synthetic.sav"
        spss_path = EXPORT_DIR / spss_filename

        success = ExportEngine.export_spss(df, spss_path)
        if success and spss_path.exists():
            with open(spss_path, "rb") as f:
                spss_bytes = f.read()
            if st.download_button(
                label="⬇️ Download SPSS File (.sav)",
                data=spss_bytes,
                file_name=spss_filename,
                mime="application/x-spss-sav",
                use_container_width=True
            ):
                _log_export(project_id, target_ds.id, "sav", str(spss_path), len(df))
        else:
            st.error("SPSS export failed or pyreadstat backend unavailable.")

    # 4. PDF Statistical Report
    with col4:
        st.markdown(
            """
            <div class="forge-card">
                <h4>📑 PDF Statistical Simulation Report</h4>
                <p style="font-size: 0.82rem; color: #64748b;">Publication-formatted academic methodology, dataset metrics, statistical tables, and ethics section.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        pdf_bytes = ExportEngine.export_pdf_report(
            project_name=active_proj.title if active_proj else "SurveyForge Project",
            df=df,
            analysis_summary=analysis_data
        )
        pdf_filename = f"SurveyForge_{target_ds.id}_Simulation_Report.pdf"

        if st.download_button(
            label="⬇️ Download Statistical Report (PDF)",
            data=pdf_bytes,
            file_name=pdf_filename,
            mime="application/pdf",
            use_container_width=True
        ):
            _log_export(project_id, target_ds.id, "pdf", str(EXPORT_DIR / pdf_filename), len(df))

    st.markdown("---")
    st.markdown("#### 🕒 Export Center History Log")
    if exports_history:
        exp_table = []
        for e in exports_history:
            exp_table.append({
                "Export ID": e.id,
                "Format": e.export_type.upper(),
                "Records Exported": e.record_count,
                "File Path": Path(e.file_path).name,
                "Exported At": e.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        st.dataframe(pd.DataFrame(exp_table), use_container_width=True, hide_index=True)
    else:
        st.write("No files downloaded or exported in this session yet.")


def _log_export(project_id: int, dataset_id: int, exp_type: str, path: str, n_records: int):
    """Log download event to database."""
    db = SessionLocal()
    try:
        eh = ExportHistory(
            project_id=project_id,
            dataset_id=dataset_id,
            export_type=exp_type,
            file_path=path,
            record_count=n_records
        )
        db.add(eh)
        db.commit()
    finally:
        db.close()

