"""
SQLAlchemy database models for SurveyForge AI.
"""
from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from database.db import Base


def utc_now():
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, default="")
    target_sample_size = Column(Integer, default=500)
    target_population = Column(String(255), default="Adults aged 18 or above in Bangladesh.")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    questionnaires = relationship("Questionnaire", back_populates="project", cascade="all, delete-orphan")
    research_variables = relationship("ResearchVariable", back_populates="project", cascade="all, delete-orphan")
    simulation_configs = relationship("SimulationConfig", back_populates="project", cascade="all, delete-orphan")
    datasets = relationship("SyntheticDataset", back_populates="project", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="project", cascade="all, delete-orphan")
    exports = relationship("ExportHistory", back_populates="project", cascade="all, delete-orphan")


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), default="google_forms")  # google_forms, csv, excel, json, manual
    source_url_or_path = Column(Text, default="")
    raw_metadata = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    project = relationship("Project", back_populates="questionnaires")
    questions = relationship("Question", back_populates="questionnaire", cascade="all, delete-orphan", order_by="Question.order_num")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False)
    question_id = Column(String(50), nullable=False)  # e.g., Q1, Q2, DEM_AGE
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # Likert Scale, Multiple Choice, Checkboxes, etc.
    answer_options = Column(Text, default="[]")  # JSON encoded list of options
    required = Column(Boolean, default=True)
    variable_name = Column(String(100), default="")  # Clean snake_case column name
    category = Column(String(100), default="General")  # Demographics, Trust, Risk, etc.
    reverse_coded = Column(Boolean, default=False)
    validation_rules = Column(Text, default="{}")  # JSON encoded rules
    order_num = Column(Integer, default=0)

    # Relationships
    questionnaire = relationship("Questionnaire", back_populates="questions")

    def get_options(self):
        try:
            return json.loads(self.answer_options) if self.answer_options else []
        except Exception:
            return []

    def set_options(self, opts_list):
        self.answer_options = json.dumps(opts_list, ensure_ascii=False)


class ResearchVariable(Base):
    __tablename__ = "research_variables"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "Trust in AI Chatbots"
    variable_type = Column(String(50), default="independent")  # independent, dependent, control, demographic
    description = Column(Text, default="")
    question_ids = Column(Text, default="[]")  # JSON list of question_id strings, e.g. ["Q16", "Q17"]
    composite_method = Column(String(50), default="mean")  # mean, sum

    # Relationships
    project = relationship("Project", back_populates="research_variables")

    def get_question_ids(self):
        try:
            return json.loads(self.question_ids) if self.question_ids else []
        except Exception:
            return []

    def set_question_ids(self, qids):
        self.question_ids = json.dumps(qids)


class SimulationConfig(Base):
    __tablename__ = "simulation_configs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    config_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    project = relationship("Project", back_populates="simulation_configs")


class SyntheticDataset(Base):
    __tablename__ = "synthetic_datasets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    record_count = Column(Integer, default=0)
    random_seed = Column(Integer, default=42)
    file_path = Column(Text, nullable=False)
    status = Column(String(50), default="generated")  # generated, validated, archived
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    project = relationship("Project", back_populates="datasets")
    metadata_rel = relationship("DatasetMetadata", back_populates="dataset", uselist=False, cascade="all, delete-orphan")
    validation_reports = relationship("ValidationReport", back_populates="dataset", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="dataset", cascade="all, delete-orphan")
    exports = relationship("ExportHistory", back_populates="dataset", cascade="all, delete-orphan")


class DatasetMetadata(Base):
    __tablename__ = "dataset_metadata"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("synthetic_datasets.id"), nullable=False, unique=True)
    generation_mode = Column(String(50), default="statistical")  # statistical, rule_based, ai_assisted
    missing_pct = Column(Float, default=0.0)
    scenario = Column(String(100), default="Baseline / Neutral")
    correlation_assumptions = Column(Text, default="{}")
    metadata_json = Column(Text, default="{}")

    # Relationships
    dataset = relationship("SyntheticDataset", back_populates="metadata_rel")


class ValidationReport(Base):
    __tablename__ = "validation_reports"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("synthetic_datasets.id"), nullable=False)
    status = Column(String(20), default="PASS")  # PASS, WARNING, FAIL
    score = Column(Float, default=100.0)
    summary_json = Column(Text, default="{}")
    details_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    dataset = relationship("SyntheticDataset", back_populates="validation_reports")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("synthetic_datasets.id"), nullable=False)
    test_name = Column(String(100), nullable=False)
    variables_used = Column(Text, default="[]")
    sample_size = Column(Integer, default=0)
    test_statistic = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    metrics_json = Column(Text, default="{}")
    interpretation = Column(Text, default="")
    limitations = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    project = relationship("Project", back_populates="analysis_results")
    dataset = relationship("SyntheticDataset", back_populates="analysis_results")


class ExportHistory(Base):
    __tablename__ = "export_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("synthetic_datasets.id"), nullable=True)
    export_type = Column(String(20), nullable=False)  # csv, excel, sav, pdf
    file_path = Column(Text, nullable=False)
    record_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    project = relationship("Project", back_populates="exports")
    dataset = relationship("SyntheticDataset", back_populates="exports")
