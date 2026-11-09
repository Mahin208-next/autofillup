"""
Synthetic Respondent Profile Generator Page for SurveyForge AI.
Enables configuring demographic and behavioral simulation parameters with distribution charts.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from core.profile_engine import ProfileEngine
from database.db import SessionLocal
from database.models import SimulationConfig


def render():
    st.markdown("<div class='section-header'><h2>👥 Synthetic Respondent Profiles & Demographics</h2><p>Configure probabilistic distributions for simulation personas. No real identities or PII are generated.</p></div>", unsafe_allow_html=True)

    project_id = st.session_state.get("current_project_id")

    st.markdown(
        """
        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 0.8rem; margin-bottom: 1rem; font-size: 0.82rem; color: #475569;">
            <strong>SIMULATION ASSUMPTION DISCLAIMER:</strong> All configured percentages below represent theoretical mathematical simulation assumptions defined by the researcher. They do NOT constitute official census or demographic claims regarding Bangladesh.
        </div>
        """,
        unsafe_allow_html=True
    )

    if "current_profile_config" not in st.session_state:
        st.session_state.current_profile_config = ProfileEngine.get_default_config()

    config = st.session_state.current_profile_config

    tab_demo, tab_digital, tab_preview = st.tabs([
        "🏙️ Demographics Configuration",
        "📱 Digital Health Behaviors",
        "👁️ Persona Preview & Distribution Visualizer"
    ])

    with tab_demo:
        st.markdown("#### Demographic Probability Distributions")

        col1, col2 = st.columns(2)

        # Age Group
        with col1:
            st.markdown("##### 🎂 Age Group Distribution (%)")
            age_d = config["demographics"]["age"]
            new_age = {}
            for k, v in age_d.items():
                new_age[k] = st.slider(f"Age: {k}", 0, 100, int(v * 100), key=f"age_{k}") / 100.0
            config["demographics"]["age"] = ProfileEngine.normalize_distribution(new_age)

        # Gender
        with col2:
            st.markdown("##### ⚧ Gender Distribution (%)")
            gen_d = config["demographics"]["gender"]
            new_gen = {}
            for k, v in gen_d.items():
                new_gen[k] = st.slider(f"Gender: {k}", 0, 100, int(v * 100), key=f"gen_{k}") / 100.0
            config["demographics"]["gender"] = ProfileEngine.normalize_distribution(new_gen)

        st.markdown("---")
        col3, col4 = st.columns(2)

        # Education
        with col3:
            st.markdown("##### 🎓 Education Level Distribution (%)")
            edu_d = config["demographics"]["education"]
            new_edu = {}
            for k, v in edu_d.items():
                new_edu[k] = st.slider(f"Edu: {k}", 0, 100, int(v * 100), key=f"edu_{k}") / 100.0
            config["demographics"]["education"] = ProfileEngine.normalize_distribution(new_edu)

        # Residence Type
        with col4:
            st.markdown("##### 🏘️ Residence Setting (%)")
            res_d = config["demographics"]["residence"]
            new_res = {}
            for k, v in res_d.items():
                new_res[k] = st.slider(f"Residence: {k}", 0, 100, int(v * 100), key=f"res_{k}") / 100.0
            config["demographics"]["residence"] = ProfileEngine.normalize_distribution(new_res)

        st.markdown("---")
        # Division
        st.markdown("##### 🗺️ Geographic Administrative Divisions (Bangladesh)")
        div_cols = st.columns(4)
        div_d = config["demographics"]["division"]
        new_div = {}
        items = list(div_d.items())
        for idx, (k, v) in enumerate(items):
            with div_cols[idx % 4]:
                new_div[k] = st.number_input(f"{k} Division (%)", min_value=1, max_value=100, value=int(v * 100), key=f"div_{k}") / 100.0
        config["demographics"]["division"] = ProfileEngine.normalize_distribution(new_div)

    with tab_digital:
        st.markdown("#### Digital Behavior Distributions")
        c_dig1, c_dig2 = st.columns(2)

        with c_dig1:
            st.markdown("##### 🤖 AI Chatbot Usage Frequency")
            ai_d = config["digital_behavior"]["ai_chatbot_frequency"]
            new_ai = {}
            for k, v in ai_d.items():
                new_ai[k] = st.slider(f"AI: {k}", 0, 100, int(v * 100), key=f"ai_{k}") / 100.0
            config["digital_behavior"]["ai_chatbot_frequency"] = ProfileEngine.normalize_distribution(new_ai)

        with c_dig2:
            st.markdown("##### 📲 Social Media Usage Frequency")
            soc_d = config["digital_behavior"]["social_media_frequency"]
            new_soc = {}
            for k, v in soc_d.items():
                new_soc[k] = st.slider(f"Social: {k}", 0, 100, int(v * 100), key=f"soc_{k}") / 100.0
            config["digital_behavior"]["social_media_frequency"] = ProfileEngine.normalize_distribution(new_soc)

        st.markdown("---")
        st.markdown("##### 🏥 Primary Healthcare Information Source")
        src_cols = st.columns(3)
        src_d = config["digital_behavior"]["primary_health_info_source"]
        new_src = {}
        for idx, (k, v) in enumerate(src_d.items()):
            with src_cols[idx % 3]:
                new_src[k] = st.number_input(f"{k} (%)", min_value=1, max_value=100, value=int(v * 100), key=f"src_{k}") / 100.0
        config["digital_behavior"]["primary_health_info_source"] = ProfileEngine.normalize_distribution(new_src)

    with tab_preview:
        st.markdown("#### 👁️ Persona Preview & Distribution Visualizer")

        prev_col1, prev_col2 = st.columns([1, 1])
        with prev_col1:
            # Distribution pie chart of age
            age_data = pd.DataFrame([{"Age Group": k, "Probability": v * 100} for k, v in config["demographics"]["age"].items()])
            fig_age = px.pie(age_data, names="Age Group", values="Probability", title="Configured Age Distribution (%)", hole=0.35)
            st.plotly_chart(fig_age, use_container_width=True)

        with prev_col2:
            # Bar chart of AI frequency
            ai_data = pd.DataFrame([{"Frequency": k, "Probability": v * 100} for k, v in config["digital_behavior"]["ai_chatbot_frequency"].items()])
            fig_ai = px.bar(ai_data, x="Frequency", y="Probability", title="Configured AI Usage Frequency (%)", color="Frequency")
            st.plotly_chart(fig_ai, use_container_width=True)

        st.markdown("##### 🎲 Sample Generated Synthetic Personas")
        sample_df = ProfileEngine.generate_profile_sample(config, n_records=6, seed=42)
        st.dataframe(sample_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("🔄 Reset to Recommended Default Distributions", use_container_width=True):
            st.session_state.current_profile_config = ProfileEngine.get_default_config()
            st.success("Reset profiles to baseline default settings.")
            st.rerun()

    with b_col2:
        if st.button("💾 Save Profile Configuration to Project", type="primary", use_container_width=True):
            db = SessionLocal()
            try:
                sc = SimulationConfig(
                    project_id=project_id,
                    name=f"Config {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
                    config_json=json.dumps(config)
                )
                db.add(sc)
                db.commit()
                st.success("Simulation profile configuration saved to project database!")
            finally:
                db.close()

