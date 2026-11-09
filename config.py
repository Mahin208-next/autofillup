"""
Configuration settings for SurveyForge AI.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Storage paths
DATA_DIR = BASE_DIR / "datasets"
EXPORT_DIR = BASE_DIR / "exports"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = BASE_DIR / "surveyforge.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Database URI
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Application Metadata
APP_NAME = "SurveyForge AI"
APP_SUBTITLE = "AI-Powered Synthetic Survey Data Generation & Statistical Analysis Platform"
APP_VERSION = "1.0.0"

# Ethical Disclaimer Constants
ETHICAL_PROVENANCE_TAG = "synthetic"
DEFAULT_DISCLAIMER = (
    "SYNTHETIC DATASET — GENERATED FOR SIMULATION AND STATISTICAL PRACTICE. "
    "NOT REAL HUMAN SURVEY RESPONSES. DOES NOT SUBMIT TO GOOGLE FORMS."
)

# Default Research Example Details
DEFAULT_PROJECT_NAME = "Trust, Perceived Risk, and Self-Medication Behavior (Bangladesh Adults)"
DEFAULT_PROJECT_TITLE = (
    "Trust, Perceived Risk, and Self-Medication Behavior: A Comparative Survey of "
    "AI Chatbots and Social Media-Based Informal Medical Advice Among Adults in Bangladesh."
)
DEFAULT_FORM_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSeuIiR-tAFvPevGgsjrwJCp8iRavWakanv6hW5LBNBmxFFbkg/viewform?usp=header"
)
DEFAULT_SAMPLE_SIZE = 500
DEFAULT_TARGET_POPULATION = "Adults aged 18 or above in Bangladesh."

# LLM / AI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "none")  # none, openai, gemini

