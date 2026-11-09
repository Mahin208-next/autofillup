"""
Tests for Data Validation Engine and Skip Logic.
"""
import pytest
import pandas as pd
import numpy as np
from core.validation_engine import ValidationEngine
from core.logic_engine import LogicEngine
from config import ETHICAL_PROVENANCE_TAG


@pytest.fixture
def clean_dataset_and_questions():
    questions = [
        {
            "question_id": "Q1",
            "question_text": "Age 18+",
            "question_type": "Multiple Choice",
            "answer_options": ["Yes", "No"],
            "required": True,
            "variable_name": "q1_18_years",
            "category": "Demographics"
        },
        {
            "question_id": "Q2",
            "question_text": "Trust in AI",
            "question_type": "Likert Scale",
            "answer_options": ["1", "2", "3", "4", "5"],
            "required": True,
            "variable_name": "q2_trust_ai",
            "category": "Trust in AI Chatbots"
        }
    ]

    df = pd.DataFrame({
        "synthetic_record_id": [f"SYNTH-{i+1:05d}" for i in range(20)],
        "data_type": [ETHICAL_PROVENANCE_TAG] * 20,
        "generation_timestamp": ["2026-11-09 12:00:00 UTC"] * 20,
        "generation_seed": [42] * 20,
        "q1_18_years": ["Yes"] * 20,
        "q2_trust_ai": [3, 4, 5, 2, 4, 3, 5, 4, 2, 3, 4, 5, 3, 4, 2, 3, 5, 4, 3, 2]
    })

    return df, questions


def test_clean_validation_pass(clean_dataset_and_questions):
    """Verify that a clean dataset passes validation with a high score."""
    df, questions = clean_dataset_and_questions
    report = ValidationEngine.validate_dataset(df, questions)

    assert report["status"] in ("PASS", "WARNING")
    assert report["score"] >= 80.0
    assert report["summary"]["passed_checks"] >= 7


def test_validation_detects_out_of_bounds_likert(clean_dataset_and_questions):
    """Verify detection of invalid Likert values (< 1 or > 5)."""
    df, questions = clean_dataset_and_questions
    # Inject out-of-range value
    df.loc[0, "q2_trust_ai"] = 99

    report = ValidationEngine.validate_dataset(df, questions)
    assert report["status"] == "FAIL"

    # Find the Likert check in details
    likert_check = next((d for d in report["details"] if "Likert" in d["check"]), None)
    assert likert_check is not None
    assert likert_check["status"] == "FAIL"


def test_validation_detects_missing_provenance(clean_dataset_and_questions):
    """Verify detection of missing or invalid data_type provenance tag."""
    df, questions = clean_dataset_and_questions
    df["data_type"] = "real_human_response"  # Illegal provenance tag

    report = ValidationEngine.validate_dataset(df, questions)
    assert report["status"] == "FAIL"
    prov_check = next((d for d in report["details"] if "Provenance" in d["check"]), None)
    assert prov_check is not None
    assert prov_check["status"] == "FAIL"


def test_logic_engine_skip_logic_and_contradiction():
    """Verify skip logic enforcement and contradiction audit."""
    rec = {
        "q10_ai_frequency": "Never used",
        "q13_used_ai_for_medicine": "Always",
        "q40_self_medication": "No",
        "q41_reasons_for_selfmed": "Saves time and money"
    }

    # Audit detects contradiction
    issues = LogicEngine.audit_record_consistency(rec)
    assert len(issues) >= 2

    # Applying skip logic fixes contradictions
    fixed_rec = LogicEngine.apply_skip_logic_and_constraints(rec, {})
    assert fixed_rec["q13_used_ai_for_medicine"] == "Never"
    assert "Not Applicable" in fixed_rec["q41_reasons_for_selfmed"]

    clean_issues = LogicEngine.audit_record_consistency(fixed_rec)
    assert len(clean_issues) == 0

