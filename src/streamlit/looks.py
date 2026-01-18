"""Defines the appearance of Streamlit app elements."""

import streamlit as st

URW_COLORS = {
    "primary": "#FFFFFF",  # White background
    "secondary": "#F8F8F8",  # Light gray
    "accent": "#E4002B",  # URW Red
    "accent_light": "#FF1744",  # Lighter red for hover
    "text": "#3C3C3C",  # Dark charcoal
    "text_muted": "#6B6B6B",  # Medium gray
    "success": "#2E7D32",  # Green for positive KPIs
    "warning": "#F57C00",  # Orange for neutral
    "danger": "#C62828",  # Dark red for negative KPIs
    "border": "#E0E0E0",  # Light border gray
}


def apply_urw_styling():
    """Apply URW corporate styling to the Streamlit app."""
    st.markdown(
        f"""
        <style>
        /* Main background */
        .stApp {{
            background-color: {URW_COLORS["primary"]};
            color: {URW_COLORS["text"]};
        }}

        /* Ensure all text elements use the theme color */
        .stMarkdown, .stMarkdown p, .stMarkdown span,
        div[data-testid="stMarkdownContainer"] p {{
            color: {URW_COLORS["text"]} !important;
        }}

        /* Headers */
        h1 {{
            color: {URW_COLORS["text"]} !important;
            font-weight: 300;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        h2, h3 {{
            color: {URW_COLORS["text"]} !important;
            font-weight: 400;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {URW_COLORS["secondary"]};
            border-right: 1px solid {URW_COLORS["border"]};
        }}

        /* Sidebar collapse/expand button - always visible */
        [data-testid="stSidebarCollapseButton"] {{
            opacity: 1 !important;
            visibility: visible !important;
        }}

        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stBaseButton-headerNoPadding"] {{
            color: {URW_COLORS["text_muted"]} !important;
            opacity: 1 !important;
        }}

        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="stBaseButton-headerNoPadding"] span {{
            color: {URW_COLORS["text_muted"]} !important;
        }}

        /* Metric cards */
        [data-testid="stMetric"] {{
            background-color: {URW_COLORS["primary"]};
            border: 1px solid {URW_COLORS["border"]};
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}

        [data-testid="stMetricLabel"] {{
            color: {URW_COLORS["text_muted"]} !important;
            text-transform: uppercase;
            font-size: 0.75rem !important;
            letter-spacing: 1px;
        }}

        [data-testid="stMetricValue"] {{
            color: {URW_COLORS["text"]} !important;
            font-weight: 600;
        }}

        /* Custom card styling */
        .mall-card {{
            background-color: {URW_COLORS["primary"]};
            border: 1px solid {URW_COLORS["border"]};
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}

        .mall-card:hover {{
            border-color: {URW_COLORS["accent"]};
            box-shadow: 0 4px 12px rgba(228, 0, 43, 0.15);
        }}

        .mall-card h3 {{
            color: {URW_COLORS["text"]} !important;
            font-weight: 500;
            margin-bottom: 8px;
        }}

        /* Store ranking table */
        .store-rank {{
            background-color: {URW_COLORS["secondary"]};
            border-radius: 6px;
            padding: 12px 15px;
            margin: 8px 0;
            display: flex;
            align-items: center;
            border-left: 3px solid {URW_COLORS["accent"]};
        }}

        .rank-number {{
            font-size: 1.2rem;
            font-weight: 600;
            color: {URW_COLORS["accent"]};
            margin-right: 15px;
            min-width: 35px;
        }}

        /* Button styling */
        .stButton > button {{
            background-color: {URW_COLORS["accent"]} !important;
            color: white !important;
            border: none;
            border-radius: 4px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.2s ease;
        }}

        .stButton > button p {{
            color: white !important;
        }}

        .stButton > button:hover {{
            background-color: {URW_COLORS["accent_light"]} !important;
            color: white !important;
            box-shadow: 0 4px 8px rgba(228, 0, 43, 0.3);
        }}

        .stButton > button:hover p {{
            color: white !important;
        }}

        /* Selectbox styling - white with gray outline and black text */
        [data-testid="stSelectbox"] {{
            color: {URW_COLORS["text"]} !important;
        }}

        [data-testid="stSelectbox"] > div > div {{
            background-color: {URW_COLORS["primary"]} !important;
            border: 1px solid {URW_COLORS["border"]} !important;
            border-radius: 4px;
            color: {URW_COLORS["text"]} !important;
        }}

        [data-testid="stSelectbox"] label {{
            color: {URW_COLORS["text"]} !important;
        }}

        [data-testid="stSelectbox"] div[data-baseweb="select"] span {{
            color: {URW_COLORS["text"]} !important;
        }}

        [data-testid="stSelectbox"] svg {{
            fill: {URW_COLORS["text"]} !important;
        }}

        /* Divider */
        hr {{
            border-color: {URW_COLORS["border"]};
        }}

        /* Trend card styling - matches st.metric exactly */
        .trend-card {{
            background-color: {URW_COLORS["primary"]};
            border: 1px solid {URW_COLORS["border"]};
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            margin-bottom: 8px;
        }}

        .trend-card-title {{
            color: {URW_COLORS["text"]};
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 12px;
            text-align: center;
        }}

        .trend-card-content {{
            display: flex;
            justify-content: space-between;
        }}

        .trend-card-side {{
            flex: 1;
            text-align: center;
            padding: 0 8px;
        }}

        .trend-card-side:first-child {{
            border-right: 1px solid {URW_COLORS["border"]};
        }}

        /* Match stMetricLabel exactly */
        .trend-card-label {{
            color: {URW_COLORS["text_muted"]} !important;
            text-transform: uppercase;
            font-size: 0.75rem !important;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        /* Match stMetricDelta exactly - Streamlit's delta styling */
        .trend-card-delta {{
            display: inline-flex;
            align-items: center;
            gap: 2px;
            font-size: 0.875rem;
            font-weight: 400;
            padding: 4px 8px;
            border-radius: 0.25rem;
            margin-bottom: 8px;
        }}

        /* Background colors for positive/negative */
        .trend-card-delta.positive {{
            background-color: rgba(33, 195, 84, 0.2) !important;
        }}

        .trend-card-delta.negative {{
            background-color: rgba(255, 43, 43, 0.2) !important;
        }}

        .trend-card-delta.neutral {{
            background-color: transparent;
        }}

        /* Arrow colors - match Streamlit metric */
        .trend-card-delta .arrow {{
            font-weight: 600;
        }}

        .trend-card-delta.positive .arrow {{
            color: #21c354 !important;
        }}

        .trend-card-delta.negative .arrow {{
            color: #ff2b2b !important;
        }}

        /* Number/percentage is always black */
        .trend-card-delta .value {{
            color: {URW_COLORS["text"]} !important;
        }}

        .trend-card-delta.neutral .value {{
            color: {URW_COLORS["text_muted"]} !important;
        }}

        .trend-card-qualifier {{
            color: {URW_COLORS["text_muted"]};
            font-size: 0.75rem;
            min-height: 2.4em;
            line-height: 1.3em;
        }}

        /* URW Logo header */
        .urw-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding-bottom: 20px;
            border-bottom: 2px solid {URW_COLORS["accent"]};
            margin-bottom: 30px;
        }}

        .urw-logo {{
            color: {URW_COLORS["accent"]};
            font-size: 2.5rem;
            font-weight: bold;
        }}

        /* Subtitle styling */
        .subtitle {{
            color: {URW_COLORS["text_muted"]};
            font-size: 1rem;
            margin-bottom: 30px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
