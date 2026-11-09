"""
Professional UI formatting, styling, and HTML components for SurveyForge AI.
"""
import streamlit as st


def apply_custom_css():
    """Inject premium CSS styling into Streamlit."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Main container max width & padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    /* Navigation styling */
    [data-testid="stSidebar"] {
        background-color: #0b192c;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #e2e8f0;
    }

    /* Custom Metric Cards */
    .forge-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .forge-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .forge-metric-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .forge-metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }
    .forge-metric-sub {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.55rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.025em;
    }
    .badge-synthetic {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .badge-pass {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .badge-warning {
        background-color: #fef9c3;
        color: #854d0e;
        border: 1px solid #fef08a;
    }
    .badge-fail {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .badge-info {
        background-color: #e0f2fe;
        color: #075985;
        border: 1px solid #bae6fd;
    }

    /* Ethical Notice Banner */
    .ethical-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
        border-left: 4px solid #38bdf8;
        padding: 0.9rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        font-size: 0.86rem;
    }
    .ethical-banner strong {
        color: #38bdf8;
    }

    /* Section Headers */
    .section-header {
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
        margin-bottom: 1.25rem;
        margin-top: 1rem;
    }
    .section-header h2 {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
    }
    .section-header p {
        font-size: 0.88rem;
        color: #64748b;
        margin: 0.2rem 0 0 0;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_ethical_banner():
    """Render the standard mandatory ethical provenance banner."""
    html = """
    <div class="ethical-banner">
        <strong>ETHICAL RESEARCH REQUIREMENT:</strong>
        All data generated in SurveyForge AI is mathematically and statistically synthesized
        for simulation, hypothesis pre-testing, and software validation.
        <strong>It is NEVER submitted to Google Forms</strong> and never imitates human respondents.
        All records carry <code>data_type = "synthetic"</code> provenance.
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(label: str, value: str or int, subtext: str = "", border_color: str = None):
    """Render a styled metric card."""
    style = f'border-top: 3px solid {border_color};' if border_color else ''
    html = f"""
    <div class="forge-card" style="{style}">
        <div class="forge-metric-label">{label}</div>
        <div class="forge-metric-value">{value}</div>
        {f'<div class="forge-metric-sub">{subtext}</div>' if subtext else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

