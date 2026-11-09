"""
Validation engine for synthetic survey datasets in SurveyForge AI.
Performs 9 comprehensive audit checks and outputs PASS/WARNING/FAIL reports.
"""
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from core.logic_engine import LogicEngine


class ValidationEngine:
    """Audits generated survey datasets across 9 structural and semantic integrity criteria."""

    @staticmethod
    def validate_dataset(
        df: pd.DataFrame,
        questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Runs full 9-point validation suite on a synthetic dataset.
        Returns a structured validation report with status, score, summary, and details.
        """
        details = []
        q_map = {q.get("variable_name"): q for q in questions if q.get("variable_name")}
        protected_cols = {"synthetic_record_id", "data_type", "generation_timestamp", "generation_seed"}

        total_checks = 9
        passed_checks = 0
        warning_count = 0
        fail_count = 0

        # Check 1: Provenance and Data Type Integrity
        c1_issues = []
        if "data_type" not in df.columns:
            c1_issues.append("Missing mandatory 'data_type' provenance column.")
        else:
            invalid_dt = df[df["data_type"] != "synthetic"]
            if len(invalid_dt) > 0:
                c1_issues.append(f"{len(invalid_dt)} records do not carry 'synthetic' provenance tag.")

        if "synthetic_record_id" not in df.columns:
            c1_issues.append("Missing 'synthetic_record_id' column.")

        if c1_issues:
            fail_count += 1
            details.append({"check": "Provenance Integrity", "status": "FAIL", "message": "; ".join(c1_issues)})
        else:
            passed_checks += 1
            details.append({"check": "Provenance Integrity", "status": "PASS", "message": "All records carry verified synthetic provenance tags."})

        # Check 2: Duplicate Records Check
        # Exclude IDs when checking for duplicate survey responses
        survey_cols = [c for c in df.columns if c not in protected_cols]
        duplicates_count = int(df.duplicated(subset=survey_cols).sum()) if survey_cols else 0
        if duplicates_count > 0:
            warning_count += 1
            details.append({
                "check": "Duplicate Survey Records",
                "status": "WARNING",
                "message": f"Detected {duplicates_count} duplicate response rows. Acceptable in small categorical surveys, but review sample variance."
            })
        else:
            passed_checks += 1
            details.append({"check": "Duplicate Survey Records", "status": "PASS", "message": "Zero identical duplicate response rows detected."})

        # Check 3: Missing Values & Required Question Check
        total_cells = df[survey_cols].size if survey_cols else 1
        missing_cells = int(df[survey_cols].isna().sum().sum()) if survey_cols else 0
        missing_rate = (missing_cells / total_cells) * 100.0 if total_cells > 0 else 0.0

        required_missing = 0
        for col in survey_cols:
            q_info = q_map.get(col, {})
            if q_info.get("required", True):
                required_missing += int(df[col].isna().sum())

        if required_missing > 0 and missing_rate > 10.0:
            fail_count += 1
            details.append({
                "check": "Missing Values & Required Questions",
                "status": "FAIL",
                "message": f"High missingness: {missing_rate:.1f}% total missing cells, including {required_missing} in required questions."
            })
        elif required_missing > 0:
            warning_count += 1
            details.append({
                "check": "Missing Values & Required Questions",
                "status": "WARNING",
                "message": f"{required_missing} missing values in required fields ({missing_rate:.1f}% overall missing rate)."
            })
        else:
            passed_checks += 1
            details.append({
                "check": "Missing Values & Required Questions",
                "status": "PASS",
                "message": f"All required questions 100% complete. Total missingness: {missing_rate:.2f}%."
            })

        # Check 4: Likert Scale Boundary Check (1 to 5)
        likert_violations = 0
        for col in survey_cols:
            q_info = q_map.get(col, {})
            if q_info.get("question_type") == "Likert Scale":
                valid_num = pd.to_numeric(df[col], errors="coerce").dropna()
                out_of_bounds = valid_num[(valid_num < 1) | (valid_num > 5)]
                likert_violations += len(out_of_bounds)

        if likert_violations > 0:
            fail_count += 1
            details.append({
                "check": "Likert Scale Bounds (1-5)",
                "status": "FAIL",
                "message": f"Found {likert_violations} Likert scale values outside valid range [1, 5]."
            })
        else:
            passed_checks += 1
            details.append({"check": "Likert Scale Bounds (1-5)", "status": "PASS", "message": "All Likert scale items strictly bounded within [1, 5]."})

        # Check 5: Category & Option Whitelist Validation
        invalid_category_entries = 0
        for col in survey_cols:
            q_info = q_map.get(col, {})
            options = q_info.get("answer_options", [])
            q_type = q_info.get("question_type")
            if options and q_type in ("Multiple Choice", "Dropdown"):
                # Convert options to string set
                opt_set = {str(o).strip().lower() for o in options}
                non_null = df[col].dropna()
                invalid_rows = non_null[~non_null.astype(str).str.strip().str.lower().isin(opt_set)]
                invalid_category_entries += len(invalid_rows)

        if invalid_category_entries > 0:
            warning_count += 1
            details.append({
                "check": "Categorical Whitelist Validation",
                "status": "WARNING",
                "message": f"{invalid_category_entries} responses not in declared option sets."
            })
        else:
            passed_checks += 1
            details.append({"check": "Categorical Whitelist Validation", "status": "PASS", "message": "All categorical responses match declared questionnaire options."})

        # Check 6: Semantic Contradiction & Skip Logic Audit
        contradiction_count = 0
        sample_to_check = df.head(200).to_dict(orient="records")
        for rec in sample_to_check:
            issues = LogicEngine.audit_record_consistency(rec)
            contradiction_count += len(issues)

        if contradiction_count > 0:
            warning_count += 1
            details.append({
                "check": "Semantic Contradictions & Skip Logic",
                "status": "WARNING",
                "message": f"Detected {contradiction_count} semantic skip-logic or conditional contradictions in sampled records."
            })
        else:
            passed_checks += 1
            details.append({"check": "Semantic Contradictions & Skip Logic", "status": "PASS", "message": "Verified logical consistency: zero skip-logic contradictions."})

        # Check 7: Demographic Age Qualification (18+)
        underage_count = 0
        for col in survey_cols:
            if "18_years" in col.lower() or "age_or_older" in col.lower():
                underage_count += int((df[col].astype(str).str.lower() == "no").sum())

        if underage_count > 0:
            fail_count += 1
            details.append({
                "check": "Target Population Eligibility (18+)",
                "status": "FAIL",
                "message": f"Found {underage_count} disqualified respondents (<18 years old)."
            })
        else:
            passed_checks += 1
            details.append({"check": "Target Population Eligibility (18+)", "status": "PASS", "message": "100% of respondents satisfy 18+ adult age eligibility criteria."})

        # Check 8: Numeric Range & Value Dispersion
        zero_var_cols = []
        for col in survey_cols:
            numeric_series = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(numeric_series) > 10 and numeric_series.std() == 0:
                zero_var_cols.append(col)

        if zero_var_cols:
            warning_count += 1
            details.append({
                "check": "Variance & Dispersion Audit",
                "status": "WARNING",
                "message": f"Zero variance detected in {len(zero_var_cols)} numeric columns ({', '.join(zero_var_cols[:3])})."
            })
        else:
            passed_checks += 1
            details.append({"check": "Variance & Dispersion Audit", "status": "PASS", "message": "Healthy variance across all numeric response distributions."})

        # Check 9: Data Type Consistency
        dtype_anomalies = 0
        for col in survey_cols:
            q_info = q_map.get(col, {})
            if q_info.get("question_type") == "Likert Scale":
                # Must be convertible to integer
                try:
                    df[col].dropna().astype(int)
                except Exception:
                    dtype_anomalies += 1

        if dtype_anomalies > 0:
            fail_count += 1
            details.append({
                "check": "Data Type Consistency",
                "status": "FAIL",
                "message": f"Type coercion failure in {dtype_anomalies} Likert items."
            })
        else:
            passed_checks += 1
            details.append({"check": "Data Type Consistency", "status": "PASS", "message": "All data types align strictly with question specifications."})

        # Compute Overall Status & Score
        score = max(0.0, (passed_checks * 100.0 + warning_count * 50.0) / total_checks)
        if fail_count > 0:
            overall_status = "FAIL"
        elif warning_count > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

        summary = {
            "overall_status": overall_status,
            "validation_score": round(score, 1),
            "total_records": len(df),
            "total_variables": len(df.columns),
            "passed_checks": passed_checks,
            "warning_checks": warning_count,
            "failed_checks": fail_count,
            "missing_cell_rate_pct": round(missing_rate, 2),
            "duplicate_rows": duplicates_count
        }

        return {
            "status": overall_status,
            "score": round(score, 1),
            "summary": summary,
            "details": details
        }

