"""
Variable mapping and composite score computation for SurveyForge AI.
"""
from typing import List, Dict, Any
import numpy as np
import pandas as pd


class QuestionMapper:
    """Handles category assignment, research variable mapping, and composite indices."""

    DEFAULT_CATEGORIES = [
        "Demographics",
        "AI Chatbot Usage",
        "Social Media Usage",
        "Trust in AI Chatbots",
        "Trust in Social Media",
        "Perceived Risk",
        "Digital Health Literacy",
        "Information Verification",
        "Healthcare Access",
        "Self-Medication Behavior",
        "General"
    ]

    @staticmethod
    def get_default_research_variables() -> List[Dict[str, Any]]:
        """Pre-configured research variables for the default Bangladesh health advice survey."""
        return [
            {
                "name": "Trust in AI Chatbots",
                "variable_type": "independent",
                "description": "Perceived trustworthiness, reliance, and credibility of AI chatbots for medical guidance.",
                "question_ids": ["Q16"],  # Matched to Likert items
                "composite_method": "mean"
            },
            {
                "name": "Trust in Social Media",
                "variable_type": "independent",
                "description": "Trust in informal medical advice shared on social media platforms.",
                "question_ids": ["Q17"],
                "composite_method": "mean"
            },
            {
                "name": "Perceived Risk of AI Advice",
                "variable_type": "independent",
                "description": "Perceived danger, adverse consequences, and uncertainty of following AI medical recommendations.",
                "question_ids": ["Q20"],
                "composite_method": "mean"
            },
            {
                "name": "Perceived Risk of Social Media Advice",
                "variable_type": "independent",
                "description": "Perceived danger and risks of following social media medical advice.",
                "question_ids": ["Q21"],
                "composite_method": "mean"
            },
            {
                "name": "Digital Health Literacy",
                "variable_type": "control",
                "description": "Ability to critically appraise, understand limitations, and evaluate online medical content.",
                "question_ids": ["Q27", "Q28"],
                "composite_method": "mean"
            },
            {
                "name": "Information Verification Behavior",
                "variable_type": "control",
                "description": "Habitual cross-checking with certified doctors or publisher credentials prior to acting.",
                "question_ids": ["Q23", "Q24", "Q25"],
                "composite_method": "mean"
            },
            {
                "name": "Self-Medication Propensity",
                "variable_type": "dependent",
                "description": "Frequency and willingness to take unprescribed drugs based on digital advice.",
                "question_ids": ["Q40", "Q46"],
                "composite_method": "mean"
            }
        ]

    @staticmethod
    def compute_composite_scores(
        df: pd.DataFrame,
        variables: List[Dict[str, Any]],
        questions_metadata: Dict[str, Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Compute composite scores for research variables across items, handling reverse coding.
        Returns the updated dataframe with composite columns added.
        """
        result_df = df.copy()

        for var in variables:
            var_name = var.get("name")
            q_ids = var.get("question_ids", [])
            method = var.get("composite_method", "mean")

            if not q_ids or not var_name:
                continue

            # Find matching column names in df
            matching_cols = []
            for col in df.columns:
                for qid in q_ids:
                    # Column name starts with qid or qid is in column
                    if col.lower().startswith(f"{qid.lower()}_") or col.lower() == qid.lower():
                        matching_cols.append(col)

            if not matching_cols:
                continue

            # Extract numeric series for each matching col
            numeric_series_list = []
            for col in matching_cols:
                # Check if question was reverse-coded
                qid = col.split("_")[0].upper()
                meta = questions_metadata.get(qid, {})
                reverse = meta.get("reverse_coded", False)
                max_scale = meta.get("validation_rules", {}).get("max", 5)

                # Convert to numeric
                series = pd.to_numeric(result_df[col], errors="coerce")
                if reverse:
                    # Standard Likert reverse: (max + min) - x, typically (5 + 1) - x = 6 - x
                    series = (max_scale + 1) - series

                numeric_series_list.append(series)

            if numeric_series_list:
                temp_matrix = pd.concat(numeric_series_list, axis=1)
                comp_col = f"COMP_{var_name.replace(' ', '_').upper()}"
                if method == "sum":
                    result_df[comp_col] = temp_matrix.sum(axis=1)
                else:
                    result_df[comp_col] = temp_matrix.mean(axis=1)

        return result_df

