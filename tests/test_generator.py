"""
Tests for Synthetic Data Generation Engine and Question Mapper.
"""
import pytest
import numpy as np
import pandas as pd
from core.synthetic_generator import SyntheticGenerator
from core.question_mapper import QuestionMapper
from config import ETHICAL_PROVENANCE_TAG


@pytest.fixture
def sample_questions():
    return [
        {
            "question_id": "Q1",
            "question_text": "Are you 18 years of age or older?",
            "question_type": "Multiple Choice",
            "answer_options": ["Yes", "No"],
            "required": True,
            "variable_name": "q1_age_18_or_older",
            "category": "Demographics"
        },
        {
            "question_id": "Q2",
            "question_text": "What is your gender?",
            "question_type": "Multiple Choice",
            "answer_options": ["Female", "Male", "Other"],
            "required": True,
            "variable_name": "q2_gender",
            "category": "Demographics"
        },
        {
            "question_id": "Q16",
            "question_text": "I believe health information provided by AI chatbots is trustworthy.",
            "question_type": "Likert Scale",
            "answer_options": ["1", "2", "3", "4", "5"],
            "required": True,
            "variable_name": "q16_trust_in_ai",
            "category": "Trust in AI Chatbots"
        },
        {
            "question_id": "Q20",
            "question_text": "How risky is it to follow medicine advice from an AI chatbot?",
            "question_type": "Likert Scale",
            "answer_options": ["1", "2", "3", "4", "5"],
            "required": True,
            "variable_name": "q20_perceived_risk_ai",
            "category": "Perceived Risk"
        }
    ]


def test_synthetic_generation_provenance_and_size(sample_questions):
    """Ensure generation produces exact sample size and mandatory provenance fields."""
    n_sample = 50
    df, meta = SyntheticGenerator.generate_dataset(
        questions=sample_questions,
        sample_size=n_sample,
        random_seed=42
    )

    assert len(df) == n_sample
    assert "synthetic_record_id" in df.columns
    assert "data_type" in df.columns
    assert "generation_timestamp" in df.columns
    assert "generation_seed" in df.columns

    # Verify all records carry synthetic provenance
    assert (df["data_type"] == ETHICAL_PROVENANCE_TAG).all()
    assert (df["generation_seed"] == 42).all()


def test_deterministic_reproducibility(sample_questions):
    """Verify that using the same random seed yields identical dataframes."""
    df1, _ = SyntheticGenerator.generate_dataset(sample_questions, sample_size=30, random_seed=123)
    df2, _ = SyntheticGenerator.generate_dataset(sample_questions, sample_size=30, random_seed=123)
    df3, _ = SyntheticGenerator.generate_dataset(sample_questions, sample_size=30, random_seed=999)

    # df1 and df2 must be identical
    pd.testing.assert_frame_equal(df1, df2)

    # df3 should differ
    assert not df1.equals(df3)


def test_missing_value_injection(sample_questions):
    """Verify missing value injection honors missing_pct."""
    df, _ = SyntheticGenerator.generate_dataset(
        sample_questions,
        sample_size=200,
        random_seed=42,
        missing_pct=10.0
    )

    survey_cols = [c for c in df.columns if c not in ("synthetic_record_id", "data_type", "generation_timestamp", "generation_seed")]
    missing_count = df[survey_cols].isna().sum().sum()
    assert missing_count > 0


def test_composite_scores_computation():
    """Test composite score computation with reverse-coding."""
    df = pd.DataFrame({
        "q1_trust": [4, 5, 3],
        "q2_neg_trust": [2, 1, 3]  # If reverse coded (max 5), 2 becomes 4, 1 becomes 5, 3 becomes 3
    })

    variables = [
        {
            "name": "Overall Trust",
            "question_ids": ["Q1", "Q2"],
            "composite_method": "mean"
        }
    ]

    q_meta = {
        "Q1": {"reverse_coded": False, "validation_rules": {"max": 5}},
        "Q2": {"reverse_coded": True, "validation_rules": {"max": 5}}
    }

    res_df = QuestionMapper.compute_composite_scores(df, variables, q_meta)
    assert "COMP_OVERALL_TRUST" in res_df.columns
    # Row 0: q1=4, q2_rev=(6-2)=4 -> mean=4.0
    # Row 1: q1=5, q2_rev=(6-1)=5 -> mean=5.0
    # Row 2: q1=3, q2_rev=(6-3)=3 -> mean=3.0
    np.testing.assert_allclose(res_df["COMP_OVERALL_TRUST"].values, [4.0, 5.0, 3.0])

