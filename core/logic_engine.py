"""
Logic engine for conditional dependencies, skip logic, and semantic constraints.
"""
from typing import Dict, Any, List
import pandas as pd


class LogicEngine:
    """Enforces questionnaire conditional dependencies and skip logic."""

    @staticmethod
    def apply_skip_logic_and_constraints(
        record: Dict[str, Any],
        questions_metadata: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply realistic survey skip-logic rules to an individual record.
        Modifies record in-place and returns it.
        """
        # Rule 1: Consent and 18+ eligibility
        for col, val in list(record.items()):
            col_l = col.lower()
            if "18_years" in col_l or "age_or_older" in col_l:
                record[col] = "Yes"  # All included study respondents must be 18+
            if "voluntarily_agree" in col_l or "consent" in col_l:
                record[col] = "Yes"  # All included respondents must consent

        # Rule 2: AI Chatbot usage skip logic
        # Find AI chatbot frequency question
        ai_freq_col = None
        for col in record:
            if "q10_" in col.lower() or ("ai" in col.lower() and "often" in col.lower() and "used" in col.lower()):
                ai_freq_col = col
                break

        if ai_freq_col:
            val = str(record[ai_freq_col]).lower()
            if "never" in val:
                # If never used AI chatbot, Q13 (used AI for medicine decision) must be Never / No
                for col in record:
                    if "q13_" in col.lower() or ("decide_what_medicin" in col.lower()):
                        record[col] = "Never"
                    if "upload" in col.lower() and "ai" in col.lower():
                        record[col] = "No"

        # Rule 3: Self-Medication skip logic
        # If Q40 (During past 12 months taken medicine without doctor prescription) is "No",
        # then Q41 (If yes, what were the main reasons) must be skipped or "Not Applicable".
        self_med_col = None
        for col in record:
            if "q40_" in col.lower() or ("without" in col.lower() and "prescription" in col.lower()):
                self_med_col = col
                break

        if self_med_col:
            val = str(record[self_med_col]).strip().lower()
            if val == "no" or "never" in val:
                for col in record:
                    if "q41_" in col.lower() or "reasons_for_selfmed" in col.lower():
                        record[col] = "Not Applicable (Did not self-medicate)"
                    if "q47_" in col.lower() or "unwanted_effect" in col.lower():
                        record[col] = "No"

        # Rule 4: Doctor consultation difficulty
        # If difficulty is "Never", barriers should reflect "No major barriers"
        for col in record:
            if "q36_" in col.lower() and "never" in str(record[col]).lower():
                for b_col in record:
                    if "q38_" in b_col.lower():
                        record[b_col] = "I do not face major difficulties"

        return record

    @staticmethod
    def audit_record_consistency(record: Dict[str, Any]) -> List[str]:
        """
        Check for logical contradictions in a single record.
        Returns a list of error/warning messages (empty if completely clean).
        """
        issues = []

        # Check self-medication contradiction
        for c1 in record:
            if "q40_" in c1.lower() and str(record[c1]).lower() == "no":
                for c2 in record:
                    if "q41_" in c2.lower():
                        val2 = str(record[c2]).lower()
                        if val2 and "not applicable" not in val2 and "none" not in val2 and val2 != "nan":
                            issues.append(f"Contradiction: Q40 is 'No' but reasons in Q41 were reported ({record[c2]}).")

        # Check AI chatbot frequency contradiction
        for c1 in record:
            if "q10_" in c1.lower() and "never" in str(record[c1]).lower():
                for c2 in record:
                    if "q13_" in c2.lower():
                        val2 = str(record[c2]).lower()
                        if val2 and "never" not in val2 and val2 != "nan":
                            issues.append(f"Contradiction: Q10 states AI never used, but Q13 indicates usage ({record[c2]}).")

        return issues

