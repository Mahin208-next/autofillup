"""
Synthetic Data Generation Engine Page for SurveyForge AI.
Supports Statistical Simulation, Rule-Based Simulation, and AI-Assisted Simulation.
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from database.db import SessionLocal
from database.models import Project, Question, SyntheticDataset, DatasetMetadata, ValidationReport, ResearchVariable
from core.synthetic_generator import SyntheticGenerator
from core.question_mapper import QuestionMapper
from core.validation_engine import ValidationEngine
from config import DATA_DIR, DEFAULT_SAMPLE_SIZE


def render():
    st.markdown("<div class='section-header'><h2>⚡ Synthetic Survey Data Generation Engine</h2><p>Synthesize statistically controlled survey records with mathematical latent models and ethical provenance.</p></div>", unsafe_allow_html=True)

    project_id = st.session_state.get("current_project_id")

    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        q_objs = (
            db.query(Question)
            .join(Question.questionnaire)
            .filter(Question.questionnaire.has(project_id=project_id))
            .order_by(Question.order_num.asc())
            .all()
        )
        questions_data = [
            {
                "question_id": q.question_id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "answer_options": q.get_options(),
                "required": q.required,
                "variable_name": q.variable_name,
                "category": q.category,
                "reverse_coded": q.reverse_coded,
                "validation_rules": json.loads(q.validation_rules) if q.validation_rules else {}
            }
            for q in q_objs
        ]
        r_vars = db.query(ResearchVariable).filter(ResearchVariable.project_id == project_id).all()
        r_vars_data = [
            {
                "name": rv.name,
                "question_ids": rv.get_question_ids(),
                "composite_method": rv.composite_method
            }
            for rv in r_vars
        ]
    finally:
        db.close()

    if not questions_data:
        st.warning("⚠️ Active project questionnaire contains no questions. Please import questions first in the Questionnaire Importer.")
        return

    st.markdown(
        """
        <div style="background: #f1f5f9; border-left: 4px solid #0284c7; padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.84rem; color: #334155; margin-bottom: 1.25rem;">
            <strong>SCIENTIFIC TRANSPARENCY NOTICE:</strong>
            Synthetic records are mathematically generated using Gaussian copula multivariate distributions.
            Latent factors model correlation patterns (e.g. Trust vs Risk).
            <strong>Configured correlations are simulation assumptions, not empirical population truths.</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_ctrl, col_info = st.columns([2, 1])

    with col_ctrl:
        st.markdown("#### 1. Simulation Mode & Parameters")

        ds_name = st.text_input("Dataset Name / Run Identifier", value=f"Sample N={DEFAULT_SAMPLE_SIZE} (Run {pd.Timestamp.now().strftime('%H%M%S')})")

        gen_mode = st.radio(
            "Generation Mode",
            options=["statistical", "rule_based", "ai_assisted"],
            format_func=lambda x: {
                "statistical": "📊 Mode 1: Statistical Simulation (Latent Factors, Copula & Distributions)",
                "rule_based": "⚙️ Mode 2: Rule-Based Simulation (Strict Conditional Logic & Constraints)",
                "ai_assisted": "🤖 Mode 3: AI-Assisted Simulation (Hypothetical Narrative Scenarios)"
            }[x]
        )

        col_sz, col_seed = st.columns(2)
        with col_sz:
            size_choice = st.selectbox(
                "Sample Size (Records to Generate)",
                options=[50, 100, 200, 300, 500, 1000, "Custom"],
                index=4  # Default 500
            )
            if size_choice == "Custom":
                final_sample_size = st.number_input("Custom Sample Size", min_value=10, max_value=25000, value=500, step=50)
            else:
                final_sample_size = int(size_choice)

        with col_seed:
            random_seed = st.number_input("Reproducibility Random Seed", min_value=0, max_value=999999, value=42, step=1)

        st.markdown("#### 2. Simulation Scenario & Assumptions")
        scenario = st.selectbox(
            "Simulation Scenario",
            options=list(SyntheticGenerator.SCENARIOS.keys())
        )
        st.caption(f"ℹ️ {SyntheticGenerator.SCENARIOS[scenario]['description']}")

        col_cor1, col_cor2 = st.columns(2)
        with col_cor1:
            corr_rt = st.slider(
                "Assumed Latent Corr: Perceived Risk ↔ Trust",
                min_value=-0.90, max_value=0.50,
                value=float(SyntheticGenerator.SCENARIOS[scenario]["latent_corr_risk_trust"]),
                step=0.05
            )
        with col_cor2:
            corr_tb = st.slider(
                "Assumed Latent Corr: Trust ↔ Self-Medication",
                min_value=-0.50, max_value=0.90,
                value=float(SyntheticGenerator.SCENARIOS[scenario]["latent_corr_trust_behavior"]),
                step=0.05
            )

        missing_pct = st.slider("Inject Missing Values (%)", min_value=0.0, max_value=15.0, value=0.0, step=0.5)

    with col_info:
        st.markdown("#### 🔬 Generation Blueprint")
        st.markdown(
            f"""
            - **Project:** {proj.name}
            - **Target Records:** `{final_sample_size}`
            - **Survey Questions:** `{len(questions_data)}`
            - **Mapped Variables:** `{len(r_vars_data)}`
            - **Random Seed:** `{random_seed}`
            - **Missing Rate:** `{missing_pct}%`
            - **Scenario:** `{scenario}`
            - **Ethical Label:** `data_type = 'synthetic'`
            """
        )

        st.markdown(
            """
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem; font-size: 0.78rem; color: #64748b;">
                <strong>Guaranteed Reproducibility:</strong> Running with the identical seed and scenario will generate exact identical data matrices every time.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Generate Action
    if st.button("🚀 Execute Synthetic Survey Generation", type="primary", use_container_width=True):
        progress_bar = st.progress(0, text="Initializing simulation engine...")

        profile_config = st.session_state.get("current_profile_config")

        progress_bar.progress(30, text="Synthesizing multivariate latent distributions...")

        custom_corrs = {
            "risk_trust": corr_rt,
            "trust_behavior": corr_tb
        }

        df_synth, meta = SyntheticGenerator.generate_dataset(
            questions=questions_data,
            sample_size=final_sample_size,
            random_seed=int(random_seed),
            generation_mode=gen_mode,
            scenario=scenario,
            missing_pct=missing_pct,
            profile_config=profile_config,
            custom_correlations=custom_corrs
        )

        progress_bar.progress(60, text="Computing theoretical composite scores...")

        # Add composite scores
        q_meta_dict = {q["question_id"]: q for q in questions_data}
        df_synth = QuestionMapper.compute_composite_scores(df_synth, r_vars_data, q_meta_dict)

        progress_bar.progress(80, text="Running 9-point validation engine...")

        # Save to file
        file_name = f"dataset_proj_{project_id}_seed_{random_seed}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = DATA_DIR / file_name
        df_synth.to_csv(file_path, index=False)

        # Validate
        val_report = ValidationEngine.validate_dataset(df_synth, questions_data)

        # Store in DB
        db = SessionLocal()
        try:
            ds_rec = SyntheticDataset(
                project_id=project_id,
                name=ds_name.strip() or f"Synthetic Sample (N={final_sample_size})",
                record_count=len(df_synth),
                random_seed=int(random_seed),
                file_path=str(file_path),
                status="validated" if val_report["status"] != "FAIL" else "generated"
            )
            db.add(ds_rec)
            db.commit()
            db.refresh(ds_rec)

            meta_rec = DatasetMetadata(
                dataset_id=ds_rec.id,
                generation_mode=gen_mode,
                missing_pct=missing_pct,
                scenario=scenario,
                correlation_assumptions=json.dumps(custom_corrs),
                metadata_json=json.dumps(meta)
            )
            db.add(meta_rec)

            rep_rec = ValidationReport(
                dataset_id=ds_rec.id,
                status=val_report["status"],
                score=val_report["score"],
                summary_json=json.dumps(val_report["summary"]),
                details_json=json.dumps(val_report["details"])
            )
            db.add(rep_rec)
            db.commit()
        finally:
            db.close()

        progress_bar.progress(100, text="Generation & Validation complete!")

        st.success(f"🎉 Generated {len(df_synth)} synthetic records successfully! Validation: **{val_report['status']}** ({val_report['score']}%)")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if st.button("📋 Open in Dataset Manager", use_container_width=True):
                st.session_state.nav_page = "📋 Dataset Manager"
                st.rerun()
        with col_g2:
            if st.button("🛡️ View Detailed Validation Report", use_container_width=True):
                st.session_state.nav_page = "🛡️ Data Validation Engine"
                st.rerun()

