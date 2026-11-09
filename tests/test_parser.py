"""
Tests for questionnaire parsing and extraction.
"""
import pytest
import json
import pandas as pd
from core.form_parser import FormParser


def test_parse_google_form_offline_and_structure():
    """Verify Google Forms parser works and extracts valid schema."""
    url = "https://docs.google.com/forms/d/e/1FAIpQLSeuIiR-tAFvPevGgsjrwJCp8iRavWakanv6hW5LBNBmxFFbkg/viewform?usp=header"
    res = FormParser.parse_google_form(url)

    assert res["success"] is True
    assert len(res["questions"]) > 0
    # Check question structure
    q1 = res["questions"][0]
    assert "question_id" in q1
    assert "question_text" in q1
    assert "question_type" in q1
    assert "answer_options" in q1
    assert "variable_name" in q1


def test_parse_csv_questionnaire(tmp_path):
    """Test importing questionnaire from a CSV file."""
    csv_file = tmp_path / "survey.csv"
    df = pd.DataFrame({
        "question_id": ["Q1", "Q2", "Q3"],
        "question_text": ["What is your age?", "Trust in medical AI?", "Do you self-medicate?"],
        "question_type": ["Multiple Choice", "Likert Scale", "Yes/No"],
        "options": ["18-24; 25-34", "1;2;3;4;5", "Yes; No"],
        "category": ["Demographics", "Trust", "Behavior"],
        "required": [True, True, False]
    })
    df.to_csv(csv_file, index=False)

    res = FormParser.parse_csv(csv_file)
    assert res["success"] is True
    assert len(res["questions"]) == 3
    assert res["questions"][1]["question_type"] == "Likert Scale"
    assert len(res["questions"][0]["answer_options"]) == 2


def test_parse_json_questionnaire():
    """Test parsing questionnaire from JSON."""
    json_data = [
        {
            "question_id": "Q1",
            "question_text": "Sample text",
            "question_type": "Likert Scale",
            "answer_options": ["1", "2", "3", "4", "5"],
            "required": True,
            "category": "Trust"
        }
    ]
    res = FormParser.parse_json(json.dumps(json_data))
    assert res["success"] is True
    assert len(res["questions"]) == 1
    assert res["questions"][0]["question_id"] == "Q1"


def test_infer_category_and_reverse_coding():
    """Test category inference heuristics and reverse coding detection."""
    assert FormParser.infer_category("What is your current age?") == "Demographics"
    assert FormParser.infer_category("Do you trust AI chatbot medical advice?") == "Trust in AI Chatbots"
    assert FormParser.infer_category("Have you taken medicine without doctor consultation?") == "Self-Medication Behavior"

    # Reverse coding detection
    assert FormParser.infer_reverse_coded("Chatbots can provide incorrect, incomplete advice") is True
    assert FormParser.infer_reverse_coded("I trust doctors completely") is False

