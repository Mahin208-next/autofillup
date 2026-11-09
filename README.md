# SurveyForge AI 🔬
### AI-Powered Synthetic Survey Data Generation & Statistical Analysis Platform

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Statistical Simulation](https://img.shields.io/badge/Simulation-Gaussian%20Copula-purple.svg)]()
[![Ethical Provenance](https://img.shields.io/badge/Provenance-Synthetic%20Verified-amber.svg)]()

**SurveyForge AI** is a professional-grade Python platform designed for academic researchers, university students, epidemiologists, and data analysts. It enables end-to-end import, dynamic parsing, probabilistic demographic configuration, statistically controlled simulation, validation, and full econometric analysis of survey instruments.

---

## ⚖️ Mandatory Ethical Provenance Notice

> **IMPORTANT ETHICAL REQUIREMENT:**
> This platform strictly synthesizes mathematical data for simulation, hypothesis pre-testing, statistical practice, and software modeling.
> - **Zero Submission:** It NEVER submits responses to Google Forms or external endpoints.
> - **Zero Impersonation:** It NEVER imitates real human respondents to inflate survey counts.
> - **Immutable Provenance:** Every generated record carries `data_type = "synthetic"`, a deterministic `generation_seed`, and an immutable timestamp.
> - **Separation of Concerns:** Real survey datasets and synthetic datasets remain strictly partitioned.

---

## 🧬 Baseline Research Project Configuration

The platform comes pre-configured with a real academic study:

- **Research Title:** *"Trust, Perceived Risk, and Self-Medication Behavior: A Comparative Survey of AI Chatbots and Social Media-Based Informal Medical Advice Among Adults in Bangladesh."*
- **Google Form URL:** `https://docs.google.com/forms/d/e/1FAIpQLSeuIiR-tAFvPevGgsjrwJCp8iRavWakanv6hW5LBNBmxFFbkg/viewform?usp=header`
- **Target Population:** Adults aged 18 or above residing in Bangladesh.
- **Default Sample Size:** $N = 500$
- **Constructs Modeled:**
  - Trust in AI Chatbots ($Q16$)
  - Trust in Social Media ($Q17$)
  - Perceived Risk of AI Advice ($Q20$)
  - Perceived Risk of Social Media Advice ($Q21$)
  - Digital Health Literacy ($Q27, Q28$)
  - Information Verification Behavior ($Q23, Q24, Q25$)
  - Self-Medication Propensity ($Q40, Q46$)

---

## 🛠️ Technology Stack

- **Core Backend:** Python 3.11+, Pandas 2.2+, NumPy, SciPy, Statsmodels
- **User Interface:** Streamlit, Custom Responsive CSS (Navy/Slate/Teal palette), Plotly Express & Graph Objects
- **Database & Persistence:** SQLite with SQLAlchemy 2.0 ORM
- **Questionnaire Ingestion:** BeautifulSoup4, Requests, Google Forms Schema Parser (`FB_PUBLIC_LOAD_DATA_`), OpenPyXL
- **Export Formats:**
  - **CSV:** Headers annotated with synthetic disclaimers and provenance.
  - **Excel (.xlsx):** Multi-sheet workbook (`Synthetic Data`, `Metadata & Assumptions`, `Validation Summary`, `Survey Codebook`).
  - **IBM SPSS (.sav):** Pyreadstat binary exporter with variable and value labels.
  - **PDF:** ReportLab publication-ready summary report.
- **Testing:** Pytest 8.0+

---

## 🏛️ Application Architecture

```
SurveyForge-AI/
├── app.py                      # Main entrypoint and navigation router
├── config.py                   # App configuration, directories, and constants
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── README.md                   # Documentation
│
├── core/                       # Core simulation & analytical engines
│   ├── form_parser.py          # Google Forms, CSV, Excel, JSON parser
│   ├── question_mapper.py      # Category classifier, construct mapper & composite scorer
│   ├── profile_engine.py       # Demographic & behavioral probability generator
│   ├── logic_engine.py         # Skip-logic, conditional dependencies & contradiction auditor
│   ├── synthetic_generator.py  # Gaussian copula latent generator (Modes 1, 2, 3)
│   ├── validation_engine.py    # 9-point structural and semantic audit suite
│   ├── statistics_engine.py    # Cronbach's alpha, correlations, t-tests, ANOVA, OLS
│   ├── visualization_engine.py # Plotly interactive charting engine
│   └── export_engine.py        # CSV, Excel, SPSS (.sav), and PDF compilation
│
├── database/                   # Database models & access service layer
│   ├── db.py                   # SQLAlchemy engine, session maker, base
│   ├── models.py               # 10 relational ORM tables
│   └── services.py             # Project seeder, aggregations, and CRUD
│
├── pages/                      # Streamlit UI modules
│   ├── dashboard.py            # Real metrics, charts, generation history
│   ├── projects.py             # Project manager (Create, edit, switch, delete)
│   ├── questionnaire.py        # Questionnaire importer & manual builder
│   ├── question_manager.py     # Item editor, category assigner & construct builder
│   ├── profiles.py             # Demographic & digital behavior probability tuning
│   ├── generator.py            # Simulation generator (Modes, sample size, seeds, correlations)
│   ├── dataset_manager.py      # Spreadsheet data grid, search, column filters
│   ├── validation.py           # 9-point audit report & quality scorecards
│   ├── analysis.py             # Descriptive stats, alpha, correlations, ANOVA, OLS
│   ├── visualization.py        # Plotly chart canvas (Bar, Pie, Hist, Box, Scatter, Heatmap)
│   ├── exports.py              # Export center (CSV, XLSX, SAV, PDF)
│   └── settings.py             # System diagnostics, AI keys, DB management
│
├── utils/                      # Helper utilities
│   ├── helpers.py              # Slugification, formatting, JSON wrappers
│   ├── validators.py           # URL & input validators
│   └── formatting.py           # Custom CSS, badges, and card renderers
│
├── tests/                      # Automated test suite (24 tests)
│   ├── test_parser.py
│   ├── test_generator.py
│   ├── test_validation.py
│   ├── test_statistics.py
│   ├── test_export.py
│   └── test_ui_smoke.py
│
├── datasets/                   # Generated synthetic dataset storage (.csv)
├── exports/                    # Exported outputs (.xlsx, .sav, .pdf)
└── assets/                     # Form schemas and static assets
```

---

## ⚡ Quickstart & Installation

### 1. Prerequisites
- Python 3.11, 3.12, 3.13, or 3.14
- Virtual environment tool (`venv` or `uv`)

### 2. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch SurveyForge AI
```bash
streamlit run app.py
```
The application will launch on `http://localhost:8501`. On first launch, it automatically seeds the default Bangladesh research project with its 42 Google Form survey items, creates the initial 500-sample synthetic dataset, and executes the validation engine.

---

## 🧪 Running Automated Tests

Run the comprehensive 24-test verification suite:
```bash
pytest -v
```
All tests verify parsing, skip logic, Gaussian copula reproducibility, Cronbach's alpha, ANOVA, linear regression, and multi-format exports.

---

## 📖 Scientific Simulation Methodology

1. **Multivariate Gaussian Copula:**
   Continuous latent scores $Z \sim \mathcal{N}_k(\mathbf{0}, \mathbf{\Sigma})$ are sampled according to theoretical correlation assumptions between Perceived Risk, Trust, Digital Health Literacy, and Self-Medication propensity.
2. **Probability Integral Transform:**
   Latent vectors are converted into uniform quantiles $U = \Phi(Z) \in [0, 1]$.
3. **Ordinal Likert Thresholding:**
   Uniform quantiles are mapped to discrete 1–5 agreement bounds with calibrated residual noise to represent psychometric measurement variation.
4. **Skip-Logic Enforcement:**
   Logical filters enforce real-world dependencies (e.g. respondents who never use AI cannot report using AI for medication selection; respondents answering 'No' to self-medication are skipped past self-medication reasons).
5. **9-Point Data Integrity Audit:**
   Each dataset undergoes automated checks for provenance tags, duplicate rows, missing rate constraints, Likert bounds $[1, 5]$, option whitelisting, semantic contradictions, adult eligibility ($18+$), variance dispersion, and data types.

---

## 📄 License
Released under the MIT License for educational, academic, and non-commercial research simulation.

