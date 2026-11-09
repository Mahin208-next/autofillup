"""
Synthetic Data Generation Engine for SurveyForge AI.
Supports Statistical Simulation, Rule-Based Simulation, and AI-Assisted Simulation.
"""
from datetime import datetime, timezone
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import norm
from core.profile_engine import ProfileEngine
from core.logic_engine import LogicEngine
from config import ETHICAL_PROVENANCE_TAG


class SyntheticGenerator:
    """Core synthesis engine for statistically controlled academic survey generation."""

    SCENARIOS = {
        "Baseline / Balanced": {
            "description": "Standard balanced distribution of trust, risk perception, and self-medication.",
            "latent_corr_risk_trust": -0.45,
            "latent_corr_trust_behavior": 0.35,
            "latent_corr_lit_risk": 0.40,
            "mean_trust": 3.1,
            "mean_risk": 3.4
        },
        "High Digital Literacy & Risk Aversion": {
            "description": "Higher education, higher critical awareness of AI errors, lower self-medication.",
            "latent_corr_risk_trust": -0.60,
            "latent_corr_trust_behavior": 0.20,
            "latent_corr_lit_risk": 0.55,
            "mean_trust": 2.6,
            "mean_risk": 4.1
        },
        "High AI Acceptance & Informal Reliance": {
            "description": "Higher reliance on AI chatbots for immediate triage due to healthcare access barriers.",
            "latent_corr_risk_trust": -0.25,
            "latent_corr_trust_behavior": 0.50,
            "latent_corr_lit_risk": 0.20,
            "mean_trust": 3.9,
            "mean_risk": 2.7
        }
    }

    @staticmethod
    def generate_dataset(
        questions: List[Dict[str, Any]],
        sample_size: int = 500,
        random_seed: int = 42,
        generation_mode: str = "statistical",  # statistical, rule_based, ai_assisted
        scenario: str = "Baseline / Balanced",
        missing_pct: float = 0.0,
        profile_config: Optional[Dict[str, Any]] = None,
        custom_correlations: Optional[Dict[str, float]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Generates a synthetic survey dataset with statistical control and ethical provenance.
        """
        rng = np.random.default_rng(random_seed)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if not profile_config:
            profile_config = ProfileEngine.get_default_config()

        scenario_params = SyntheticGenerator.SCENARIOS.get(
            scenario, SyntheticGenerator.SCENARIOS["Baseline / Balanced"]
        )

        corr_risk_trust = scenario_params["latent_corr_risk_trust"]
        corr_trust_behavior = scenario_params["latent_corr_trust_behavior"]

        if custom_correlations:
            if "risk_trust" in custom_correlations:
                corr_risk_trust = float(custom_correlations["risk_trust"])
            if "trust_behavior" in custom_correlations:
                corr_trust_behavior = float(custom_correlations["trust_behavior"])

        # 1. Generate Latent Factor Scores (Gaussian Copula)
        # Latents: [0: Trust_AI, 1: Trust_Social, 2: Perceived_Risk_AI, 3: Perceived_Risk_Social, 4: Literacy, 5: Self_Med_Propensity]
        cov_matrix = np.array([
            # T_AI,  T_Soc, R_AI,  R_Soc, Lit,   SM_Prop
            [ 1.00,  0.40, -0.45, -0.25, -0.15,  0.30],  # Trust_AI
            [ 0.40,  1.00, -0.20, -0.40, -0.25,  0.35],  # Trust_Social
            [-0.45, -0.20,  1.00,  0.55,  0.35, -0.30],  # Perceived_Risk_AI
            [-0.25, -0.40,  0.55,  1.00,  0.30, -0.25],  # Perceived_Risk_Social
            [-0.15, -0.25,  0.35,  0.30,  1.00, -0.35],  # Literacy
            [ 0.30,  0.35, -0.30, -0.25, -0.35,  1.00]   # Self_Med_Propensity
        ])

        # Adjust according to scenario
        cov_matrix[0, 2] = cov_matrix[2, 0] = corr_risk_trust
        cov_matrix[0, 5] = cov_matrix[5, 0] = corr_trust_behavior

        # Ensure positive semi-definite
        min_eig = np.min(np.real(np.linalg.eigvals(cov_matrix)))
        if min_eig < 1e-4:
            cov_matrix -= 1.1 * min_eig * np.eye(cov_matrix.shape[0])

        latent_vectors = rng.multivariate_normal(
            mean=[0, 0, 0, 0, 0, 0],
            cov=cov_matrix,
            size=sample_size
        )

        # Standard normal CDF transforms to uniform [0, 1]
        latent_uniform = norm.cdf(latent_vectors)

        # 2. Build rows
        records = []
        q_meta_map = {q.get("question_id"): q for q in questions}

        for i in range(sample_size):
            rec_id = f"SYNTH-{i+1:05d}"
            row = {
                "synthetic_record_id": rec_id,
                "data_type": ETHICAL_PROVENANCE_TAG,
                "generation_timestamp": timestamp_str,
                "generation_seed": random_seed
            }

            u_trust_ai = latent_uniform[i, 0]
            u_trust_soc = latent_uniform[i, 1]
            u_risk_ai = latent_uniform[i, 2]
            u_risk_soc = latent_uniform[i, 3]
            u_lit = latent_uniform[i, 4]
            u_sm_prop = latent_uniform[i, 5]

            # Sample each question
            for q in questions:
                var_name = q.get("variable_name") or f"q_{q.get('question_id', 'var')}"
                q_type = q.get("question_type", "Multiple Choice")
                options = q.get("answer_options", [])
                category = q.get("category", "")
                text = (q.get("question_text") or "").lower()

                # Map Demographics using ProfileEngine if available
                if category == "Demographics" or any(w in text for w in ["age", "gender", "education", "division", "occupation", "situation"]):
                    val = SyntheticGenerator._sample_demographic(text, profile_config, rng)
                    if val is not None:
                        row[var_name] = val
                        continue

                # Map based on question type
                if q_type == "Likert Scale" or (len(options) == 5 and any(str(x) in options[0] for x in ["1", "Strongly"])):
                    # Determine appropriate latent factor
                    if "ai" in text and ("trust" in text or "rely" in text):
                        u_val = u_trust_ai
                    elif "social" in text and ("trust" in text or "rely" in text):
                        u_val = u_trust_soc
                    elif "ai" in text and ("risk" in text or "harm" in text):
                        u_val = u_risk_ai
                    elif "social" in text and ("risk" in text or "harm" in text):
                        u_val = u_risk_soc
                    elif "literacy" in text or "check" in text or "verif" in text or "tell" in text:
                        u_val = u_lit
                    else:
                        u_val = rng.uniform(0, 1)

                    # Add slight noise to simulate measurement residual
                    noisy_u = np.clip(u_val + rng.normal(0, 0.08), 0.001, 0.999)
                    # Convert uniform quantile into 1..5 Likert integer score
                    score = int(math.floor(noisy_u * 5)) + 1
                    row[var_name] = score

                elif q_type in ("Multiple Choice", "Dropdown"):
                    if not options:
                        row[var_name] = "Yes" if "agree" in text else "Option A"
                    else:
                        # Weight selection based on latent factor
                        if "self-medicat" in text or "without professional" in text:
                            # Higher u_sm_prop = higher chance of Yes
                            prob_yes = np.clip(0.20 + 0.55 * u_sm_prop, 0.05, 0.95)
                            row[var_name] = "Yes" if rng.uniform() < prob_yes else "No"
                        elif "often have you used an ai" in text:
                            probs = [0.15, 0.28, 0.32, 0.25] if len(options) == 4 else [0.10, 0.20, 0.30, 0.25, 0.15][:len(options)]
                            probs = np.array(probs) / sum(probs)
                            row[var_name] = rng.choice(options, p=probs)
                        else:
                            row[var_name] = rng.choice(options)

                elif q_type == "Checkboxes":
                    # For checkboxes, select 1 to 3 plausible items
                    if options:
                        k = rng.integers(1, min(4, len(options) + 1))
                        chosen = rng.choice(options, size=k, replace=False)
                        row[var_name] = "; ".join(chosen)
                    else:
                        row[var_name] = "None"

                elif q_type in ("Linear Scale", "Numeric"):
                    rules = q.get("validation_rules", {})
                    min_val = rules.get("min", 1)
                    max_val = rules.get("max", 5)
                    row[var_name] = int(rng.integers(min_val, max_val + 1))

                elif q_type == "Yes/No":
                    row[var_name] = rng.choice(["Yes", "No"], p=[0.55, 0.45])

                elif q_type in ("Short Answer", "Paragraph"):
                    # Realistic synthetic survey response statements (no personal identifiers)
                    sample_remarks = [
                        "I sometimes verify medical terms before consulting a clinic.",
                        "Doctors give better personalized diagnoses than AI.",
                        "AI is faster for general knowledge, but risks are high.",
                        "Affordability and long wait queues in hospitals are major factors.",
                        "No additional comments."
                    ]
                    row[var_name] = rng.choice(sample_remarks)
                else:
                    row[var_name] = rng.choice(options) if options else "N/A"

            # Apply rule-based skip logic and constraints
            if generation_mode in ("rule_based", "statistical", "ai_assisted"):
                row = LogicEngine.apply_skip_logic_and_constraints(row, q_meta_map)

            records.append(row)

        df = pd.DataFrame(records)

        # 3. Apply missing values injection if requested
        if missing_pct > 0.0:
            df = SyntheticGenerator._inject_missing_values(df, missing_pct, rng)

        metadata = {
            "record_count": sample_size,
            "random_seed": random_seed,
            "generation_mode": generation_mode,
            "scenario": scenario,
            "missing_pct": missing_pct,
            "correlation_assumptions": {
                "risk_trust_latent": corr_risk_trust,
                "trust_behavior_latent": corr_trust_behavior
            },
            "timestamp": timestamp_str
        }

        return df, metadata

    @staticmethod
    def _sample_demographic(text: str, config: Dict[str, Any], rng: np.random.Generator) -> Optional[str]:
        """Match question text to demographic configuration distribution."""
        dem = config.get("demographics", {})
        if "age" in text:
            return ProfileEngine.sample_category(dem.get("age", {}), size=1, rng=rng)[0]
        if "gender" in text:
            return ProfileEngine.sample_category(dem.get("gender", {}), size=1, rng=rng)[0]
        if "education" in text:
            return ProfileEngine.sample_category(dem.get("education", {}), size=1, rng=rng)[0]
        if "live" in text or "residence" in text:
            return ProfileEngine.sample_category(dem.get("residence", {}), size=1, rng=rng)[0]
        if "situation" in text or "occupation" in text or "describe" in text:
            return ProfileEngine.sample_category(dem.get("occupation", {}), size=1, rng=rng)[0]
        if "income" in text:
            return ProfileEngine.sample_category(dem.get("income", {}), size=1, rng=rng)[0]
        if "division" in text:
            return ProfileEngine.sample_category(dem.get("division", {}), size=1, rng=rng)[0]
        return None

    @staticmethod
    def _inject_missing_values(df: pd.DataFrame, missing_pct: float, rng: np.random.Generator) -> pd.DataFrame:
        """Inject missing values (NaN) only into survey questions, preserving provenance fields."""
        df_copy = df.copy()
        protected = {"synthetic_record_id", "data_type", "generation_timestamp", "generation_seed"}
        target_cols = [c for c in df_copy.columns if c not in protected]

        frac = min(max(missing_pct / 100.0, 0.0), 0.50)
        for col in target_cols:
            mask = rng.uniform(0, 1, size=len(df_copy)) < frac
            df_copy.loc[mask, col] = np.nan

        return df_copy
