"""
End-to-end integration test for the complete SurveyForge AI research workflow.
Covers: Project -> Questionnaire -> Generation -> Validation -> Statistics -> Exports.
"""
import pytest
from pathlib import Path
import json
import pandas as pd
from database.db import SessionLocal, init_db
from database.models import Project, Questionnaire, Question, ResearchVariable, SyntheticDataset
from core.form_parser import FormParser
from core.question_mapper import QuestionMapper
from core.synthetic_generator import SyntheticGenerator
from core.validation_engine import ValidationEngine
from core.statistics_engine import StatisticsEngine
from core.export_engine import ExportEngine
from config import DATA_DIR, EXPORT_DIR, ETHICAL_PROVENANCE_TAG


def test_complete_end_to_end_research_pipeline(tmp_path):
    """Execute complete end-to-end research simulation and analysis workflow."""
    init_db()
    db = SessionLocal()

    try:
        # Step 1: Create Project
        proj = Project(
            name="E2E Pipeline Test Project",
            title="Assessing AI Health Consultation Patterns",
            target_sample_size=100,
            target_population="Adults aged 18+ in Bangladesh"
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)
        assert proj.id is not None

        # Step 2: Import Questionnaire from CSV template
        csv_template = Path("assets/sample_questionnaire_template.csv")
        assert csv_template.exists()
        parsed = FormParser.parse_csv(csv_template)
        assert parsed["success"] is True
        assert len(parsed["questions"]) > 0

        q_parent = Questionnaire(
            project_id=proj.id,
            title="E2E Survey Instrument",
            source_type="csv"
        )
        db.add(q_parent)
        db.commit()
        db.refresh(q_parent)

        q_list = []
        for q in parsed["questions"]:
            q_obj = Question(
                questionnaire_id=q_parent.id,
                question_id=q["question_id"],
                question_text=q["question_text"],
                question_type=q["question_type"],
                answer_options=json.dumps(q["answer_options"]),
                required=q["required"],
                variable_name=q["variable_name"],
                category=q["category"],
                reverse_coded=q["reverse_coded"],
                order_num=q["order_num"]
            )
            db.add(q_obj)
            q_list.append(q)
        db.commit()

        # Step 3: Define Research Variable
        r_var = ResearchVariable(
            project_id=proj.id,
            name="Trust in AI Construct",
            variable_type="independent",
            composite_method="mean"
        )
        r_var.set_question_ids(["TR_AI_01", "TR_AI_02"])
        db.add(r_var)
        db.commit()

        # Step 4: Generate Synthetic Dataset (N=100)
        df, meta = SyntheticGenerator.generate_dataset(
            questions=q_list,
            sample_size=100,
            random_seed=42,
            generation_mode="statistical",
            scenario="Baseline / Balanced"
        )
        assert len(df) == 100
        assert (df["data_type"] == ETHICAL_PROVENANCE_TAG).all()

        # Step 5: Compute Composite Scores
        q_meta = {q["question_id"]: q for q in q_list}
        df_comp = QuestionMapper.compute_composite_scores(
            df,
            [{"name": "Trust in AI Construct", "question_ids": ["TR_AI_01", "TR_AI_02"], "composite_method": "mean"}],
            q_meta
        )
        assert "COMP_TRUST_IN_AI_CONSTRUCT" in df_comp.columns

        # Step 6: 9-Point Validation Audit
        val_rep = ValidationEngine.validate_dataset(df_comp, q_list)
        assert val_rep["status"] in ("PASS", "WARNING")
        assert val_rep["score"] >= 80.0

        # Step 7: Statistical Analysis (Descriptive, Reliability, Regression)
        # Cronbach's Alpha
        likert_cols = [c for c in df_comp.columns if "tr_ai_" in c.lower()]
        if len(likert_cols) >= 2:
            rel_res = StatisticsEngine.cronbach_alpha(df_comp, likert_cols)
            assert "alpha" in rel_res
            assert 0.0 <= rel_res["alpha"] <= 1.0

        # Descriptive Statistics
        desc = StatisticsEngine.descriptive_stats(df_comp["COMP_TRUST_IN_AI_CONSTRUCT"])
        assert desc["is_numeric"] is True
        assert desc["sample_size"] == 100

        # Step 8: Multi-Format Exports
        csv_out = tmp_path / "e2e_dataset.csv"
        ExportEngine.export_csv(df_comp, csv_out)
        assert csv_out.exists()

        xlsx_out = tmp_path / "e2e_dataset.xlsx"
        ExportEngine.export_excel(df_comp, meta, val_rep["summary"], q_list, xlsx_out)
        assert xlsx_out.exists()

        sav_out = tmp_path / "e2e_dataset.sav"
        spss_ok = ExportEngine.export_spss(df_comp, sav_out)
        assert spss_ok is True
        assert sav_out.exists()

        pdf_out = tmp_path / "e2e_report.pdf"
        pdf_bytes = ExportEngine.export_pdf_report(
            proj.title,
            df_comp,
            [{"test_name": "Cronbach's Alpha", "test_statistic": 0.82, "p_value": None, "interpretation": "High consistency"}],
            pdf_out
        )
        assert pdf_out.exists()
        assert len(pdf_bytes) > 0

    finally:
        # Cleanup test project
        db.delete(proj)
        db.commit()
        db.close()
