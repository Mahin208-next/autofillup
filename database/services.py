"""
Data access service layer for SurveyForge AI.
Handles project initialization, default project seeding, and database transactions.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from database.db import SessionLocal, init_db
from database.models import (
    Project, Questionnaire, Question, ResearchVariable, SimulationConfig,
    SyntheticDataset, DatasetMetadata, ValidationReport, AnalysisResult, ExportHistory
)
from core.form_parser import FormParser
from core.question_mapper import QuestionMapper
from core.synthetic_generator import SyntheticGenerator
from core.validation_engine import ValidationEngine
from config import (
    DEFAULT_PROJECT_NAME, DEFAULT_PROJECT_TITLE, DEFAULT_FORM_URL,
    DEFAULT_SAMPLE_SIZE, DEFAULT_TARGET_POPULATION, DATA_DIR
)


class ProjectService:
    """Manages project lifecycles, default seeding, and data persistence."""

    @staticmethod
    def ensure_initialized():
        """Initialize DB tables and seed default research project if not existing."""
        init_db()
        db = SessionLocal()
        try:
            default_proj = db.query(Project).filter(Project.is_default == True).first()
            if not default_proj:
                ProjectService.seed_default_project(db)
        finally:
            db.close()

    @staticmethod
    def seed_default_project(db) -> Project:
        """Seed the required default research project with actual Google Forms questionnaire."""
        proj = Project(
            name=DEFAULT_PROJECT_NAME,
            title=DEFAULT_PROJECT_TITLE,
            description=(
                "Academic comparative survey investigating adult trust, risk perceptions, "
                "digital health literacy, and self-medication decisions regarding AI chatbots "
                "vs. social media-based informal medical advice in Bangladesh."
            ),
            target_sample_size=DEFAULT_SAMPLE_SIZE,
            target_population=DEFAULT_TARGET_POPULATION,
            is_default=True
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)

        # Parse questionnaire (uses cached or live Google Form)
        parsed = FormParser.parse_google_form(DEFAULT_FORM_URL)
        q_items = parsed.get("questions", [])

        # Create Questionnaire record
        q_record = Questionnaire(
            project_id=proj.id,
            title=parsed.get("title", "Trust, Risk & Self-Medication Survey Questionnaire"),
            source_type="google_forms",
            source_url_or_path=DEFAULT_FORM_URL,
            raw_metadata=json.dumps({"cached": parsed.get("is_cached", False)})
        )
        db.add(q_record)
        db.commit()
        db.refresh(q_record)

        # Insert Question records
        for item in q_items:
            q_obj = Question(
                questionnaire_id=q_record.id,
                question_id=item["question_id"],
                question_text=item["question_text"],
                question_type=item["question_type"],
                answer_options=json.dumps(item["answer_options"], ensure_ascii=False),
                required=item.get("required", True),
                variable_name=item["variable_name"],
                category=item["category"],
                reverse_coded=item.get("reverse_coded", False),
                validation_rules=json.dumps(item.get("validation_rules", {})),
                order_num=item["order_num"]
            )
            db.add(q_obj)
        db.commit()

        # Insert Default Research Variables
        for rv in QuestionMapper.get_default_research_variables():
            r_obj = ResearchVariable(
                project_id=proj.id,
                name=rv["name"],
                variable_type=rv["variable_type"],
                description=rv["description"],
                question_ids=json.dumps(rv["question_ids"]),
                composite_method=rv["composite_method"]
            )
            db.add(r_obj)
        db.commit()

        # Generate Initial Default Synthetic Dataset (500 records)
        df, meta = SyntheticGenerator.generate_dataset(
            questions=q_items,
            sample_size=DEFAULT_SAMPLE_SIZE,
            random_seed=42,
            generation_mode="statistical",
            scenario="Baseline / Balanced"
        )

        dataset_path = DATA_DIR / f"dataset_proj_{proj.id}_default.csv"
        df.to_csv(dataset_path, index=False)

        ds_record = SyntheticDataset(
            project_id=proj.id,
            name="Baseline 500 Synthetic Sample (Seed 42)",
            record_count=len(df),
            random_seed=42,
            file_path=str(dataset_path),
            status="generated"
        )
        db.add(ds_record)
        db.commit()
        db.refresh(ds_record)

        meta_record = DatasetMetadata(
            dataset_id=ds_record.id,
            generation_mode="statistical",
            missing_pct=0.0,
            scenario="Baseline / Balanced",
            correlation_assumptions=json.dumps(meta.get("correlation_assumptions", {})),
            metadata_json=json.dumps(meta)
        )
        db.add(meta_record)

        # Run and store initial validation
        val_res = ValidationEngine.validate_dataset(df, q_items)
        val_rep = ValidationReport(
            dataset_id=ds_record.id,
            status=val_res["status"],
            score=val_res["score"],
            summary_json=json.dumps(val_res["summary"]),
            details_json=json.dumps(val_res["details"])
        )
        db.add(val_rep)
        db.commit()

        # Seed initial baseline statistical analyses
        try:
            from core.statistics_engine import StatisticsEngine
            likert_cols = [c for c in df.columns if ("trust" in c.lower() or "risk" in c.lower()) and "comp_" not in c.lower()]
            if len(likert_cols) >= 2:
                # 1. Cronbach's Alpha
                alpha_res = StatisticsEngine.cronbach_alpha(df, likert_cols[:4])
                db.add(AnalysisResult(
                    project_id=proj.id,
                    dataset_id=ds_record.id,
                    test_name=alpha_res["test_name"],
                    variables_used=json.dumps(likert_cols[:4]),
                    sample_size=alpha_res["sample_size"],
                    test_statistic=alpha_res["alpha"],
                    p_value=None,
                    metrics_json=json.dumps(alpha_res, default=str),
                    interpretation=alpha_res["interpretation"],
                    limitations=alpha_res["limitations"]
                ))

            # 2. Linear Regression (Trust predicting Self-Medication)
            num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors="coerce")) and c not in ("synthetic_record_id", "generation_seed")]
            if len(num_cols) >= 3:
                reg_res = StatisticsEngine.linear_regression(df, num_cols[0], num_cols[1:3])
                if "error" not in reg_res:
                    db.add(AnalysisResult(
                        project_id=proj.id,
                        dataset_id=ds_record.id,
                        test_name=reg_res["test_name"],
                        variables_used=json.dumps([num_cols[0]] + num_cols[1:3]),
                        sample_size=reg_res["sample_size"],
                        test_statistic=reg_res["f_statistic"],
                        p_value=reg_res["p_value"],
                        metrics_json=json.dumps(reg_res, default=str),
                        interpretation=reg_res["interpretation"],
                        limitations=reg_res["limitations"]
                    ))

            db.commit()
        except Exception as e:
            print(f"Notice: Initial statistical seeding skipped ({e})")

        return proj

    @staticmethod
    def get_dashboard_metrics(project_id: Optional[int] = None) -> Dict[str, Any]:
        """Aggregate actual real metrics across database for dashboard."""
        db = SessionLocal()
        try:
            total_projects = db.query(Project).count()
            total_records = 0
            datasets = db.query(SyntheticDataset).all()
            for ds in datasets:
                total_records += ds.record_count

            # Questions count
            total_questions = db.query(Question).count()
            # Variables count
            total_variables = db.query(ResearchVariable).count()

            # Latest validation status
            latest_val = db.query(ValidationReport).order_by(ValidationReport.id.desc()).first()
            val_status = latest_val.status if latest_val else "Not Validated"
            val_score = latest_val.score if latest_val else 0.0

            # Recent datasets
            recent_ds = (
                db.query(SyntheticDataset)
                .order_by(SyntheticDataset.id.desc())
                .limit(5)
                .all()
            )
            recent_list = []
            for r in recent_ds:
                recent_list.append({
                    "id": r.id,
                    "name": r.name,
                    "records": r.record_count,
                    "seed": r.random_seed,
                    "date": r.created_at.strftime("%Y-%m-%d %H:%M")
                })

            return {
                "total_projects": total_projects,
                "total_questions": total_questions,
                "total_records": total_records,
                "total_variables": total_variables,
                "validation_status": val_status,
                "validation_score": val_score,
                "recent_datasets": recent_list
            }
        finally:
            db.close()

