"""
Synthetic respondent profile engine for SurveyForge AI.
Defines user-configurable simulation probability distributions.
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd


class ProfileEngine:
    """Manages synthetic demographic and behavioral profile distributions."""

    DEFAULT_PROFILES = {
        "demographics": {
            "age": {
                "18–24 years": 0.35,
                "25–34 years": 0.30,
                "35–44 years": 0.20,
                "45+ years": 0.15
            },
            "gender": {
                "Female": 0.48,
                "Male": 0.51,
                "Prefer not to say / Other": 0.01
            },
            "education": {
                "Secondary (SSC) or below": 0.12,
                "Higher Secondary (HSC)": 0.22,
                "Bachelor's Degree": 0.45,
                "Master's Degree or above": 0.21
            },
            "occupation": {
                "Student": 0.32,
                "Private Sector Employee": 0.35,
                "Government / Public Sector": 0.10,
                "Business / Self-Employed": 0.13,
                "Homemaker / Unemployed": 0.10
            },
            "income": {
                "Under 15,000 BDT": 0.25,
                "15,000 – 30,000 BDT": 0.35,
                "30,001 – 60,000 BDT": 0.25,
                "Above 60,000 BDT": 0.15
            },
            "division": {
                "Dhaka": 0.42,
                "Chattogram": 0.20,
                "Rajshahi": 0.10,
                "Khulna": 0.08,
                "Sylhet": 0.07,
                "Barishal": 0.05,
                "Rangpur": 0.05,
                "Mymensingh": 0.03
            },
            "residence": {
                "Urban (Metropolitan / City Corporation)": 0.62,
                "Semi-Urban (District / Upazila Municipality)": 0.25,
                "Rural": 0.13
            }
        },
        "digital_behavior": {
            "daily_internet_hours": {
                "1–2 hours": 0.15,
                "3–5 hours": 0.52,
                "6+ hours": 0.33
            },
            "social_media_frequency": {
                "Multiple times a day": 0.68,
                "Once daily": 0.22,
                "Few times a week": 0.08,
                "Rarely / Never": 0.02
            },
            "ai_chatbot_frequency": {
                "Daily": 0.18,
                "Several times a week": 0.32,
                "Once a week or less": 0.28,
                "Never": 0.22
            },
            "primary_health_info_source": {
                "Qualified Medical Professional / Doctor": 0.46,
                "AI Chatbot (e.g., ChatGPT, Claude)": 0.16,
                "Social Media (Facebook, YouTube)": 0.14,
                "Friends, Family, or Elders": 0.14,
                "Local Pharmacy Storekeeper": 0.10
            }
        }
    }

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Return a fresh copy of default profile distributions."""
        import copy
        return copy.deepcopy(ProfileEngine.DEFAULT_PROFILES)

    @staticmethod
    def normalize_distribution(dist: Dict[str, float]) -> Dict[str, float]:
        """Ensure probabilities sum strictly to 1.0."""
        total = sum(dist.values())
        if total <= 0:
            count = len(dist)
            return {k: 1.0 / count for k in dist}
        return {k: float(v) / total for k, v in dist.items()}

    @staticmethod
    def sample_category(dist: Dict[str, float], size: int = 1, rng: np.random.Generator = None) -> List[str]:
        """Sample values according to categorical distribution."""
        if rng is None:
            rng = np.random.default_rng()
        norm_dist = ProfileEngine.normalize_distribution(dist)
        keys = list(norm_dist.keys())
        probs = list(norm_dist.values())
        return list(rng.choice(keys, size=size, p=probs))

    @staticmethod
    def generate_profile_sample(config: Dict[str, Any], n_records: int = 5, seed: int = 42) -> pd.DataFrame:
        """Generate a small preview dataframe of respondent demographic profiles."""
        rng = np.random.default_rng(seed)
        data = {}

        demographics = config.get("demographics", {})
        for trait, dist in demographics.items():
            data[trait.capitalize()] = ProfileEngine.sample_category(dist, size=n_records, rng=rng)

        digital = config.get("digital_behavior", {})
        for trait, dist in digital.items():
            label = trait.replace("_", " ").title()
            data[label] = ProfileEngine.sample_category(dist, size=n_records, rng=rng)

        return pd.DataFrame(data)

