"""
Tests for Export Center (CSV, Excel, SPSS, PDF).
"""
import pytest
from pathlib import Path
import pandas as pd
from core.export_engine import ExportEngine
from config import DEFAULT_DISCLAIMER, ETHICAL_PROVENANCE_TAG


@pytest.fixture
def sample_export_data():
    df = pd.DataFrame({
        "synthetic_record_id": ["SYNTH-001", "SYNTH-002", "SYNTH-003"],
        "data_type": [ETHICAL_PROVENANCE_TAG] * 3,
        "age": ["18-24", "25-34", "35-44"],
        "trust_score": [3.5, 4.2, 2.8]
    })
    meta = {
        "random_seed": 42,
        "scenario": "Baseline",
        "generation_mode": "statistical",
        "timestamp": "2026-11-09 12:00:00"
    }
    val = {
        "overall_status": "PASS",
        "validation_score": 100.0,
        "total_records": 3
    }
    questions = [
        {"question_id": "Q1", "variable_name": "age", "question_text": "Age", "question_type": "Multiple Choice"}
    ]
    return df, meta, val, questions


def test_csv_export(sample_export_data, tmp_path):
    """Verify CSV export includes disclaimer header and valid records."""
    df, meta, val, q = sample_export_data
    out_file = tmp_path / "test.csv"
    csv_bytes = ExportEngine.export_csv(df, out_file)

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert DEFAULT_DISCLAIMER in content
    assert "data_type='synthetic'" in content
    assert "SYNTH-001" in content


def test_excel_export_multi_sheet(sample_export_data, tmp_path):
    """Verify Excel export creates 4 distinct sheets with metadata and codebook."""
    df, meta, val, q = sample_export_data
    out_file = tmp_path / "test.xlsx"
    excel_bytes = ExportEngine.export_excel(df, meta, val, q, out_file)

    assert out_file.exists()
    xl = pd.ExcelFile(out_file)
    assert "Synthetic Data" in xl.sheet_names
    assert "Metadata & Assumptions" in xl.sheet_names
    assert "Validation Summary" in xl.sheet_names
    assert "Survey Codebook" in xl.sheet_names

    read_data = pd.read_excel(out_file, sheet_name="Synthetic Data")
    assert len(read_data) == 3


def test_spss_export(sample_export_data, tmp_path):
    """Verify SPSS .sav file creation via pyreadstat."""
    df, _, _, _ = sample_export_data
    out_file = tmp_path / "test.sav"
    success = ExportEngine.export_spss(df, out_file)

    assert success is True
    assert out_file.exists()
    assert out_file.stat().st_size > 0


def test_pdf_report_export(sample_export_data, tmp_path):
    """Verify PDF compilation with ReportLab."""
    df, _, _, _ = sample_export_data
    out_file = tmp_path / "report.pdf"
    analysis_data = [
        {"test_name": "T-Test", "test_statistic": 2.45, "p_value": 0.015, "interpretation": "Significant effect"}
    ]
    pdf_bytes = ExportEngine.export_pdf_report("Test Study", df, analysis_data, out_file)

    assert out_file.exists()
    assert out_file.stat().st_size > 1000
    # PDF signature %PDF
    assert pdf_bytes.startswith(b"%PDF")

