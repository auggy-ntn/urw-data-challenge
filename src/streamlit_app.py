"""URW Mall Analytics Dashboard.

Streamlit app for visualizing mall and store KPIs.
"""

import streamlit as st

# =============================================================================
# URW BRANDING & CONFIGURATION
# =============================================================================

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

        .stButton > button:hover {{
            background-color: {URW_COLORS["accent_light"]} !important;
            box-shadow: 0 4px 8px rgba(228, 0, 43, 0.3);
        }}

        /* Divider */
        hr {{
            border-color: {URW_COLORS["border"]};
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


# =============================================================================
# DATA LOADING PLACEHOLDERS
# =============================================================================


@st.cache_data
def load_malls():
    """Load mall dimension data.

    Returns:
        list: List of mall dictionaries with id, name, country, etc.
    """
    # TODO: Replace with actual data loading from data/raw/dim_malls_v1.csv
    # Example structure:
    return [
        {"id": 1, "name": "Westfield Euralille", "country": "FR", "city": "Lille"},
        {"id": 2, "name": "Westfield Parly 2", "country": "FR", "city": "Le Chesnay"},
        {"id": 3, "name": "Westfield Vélizy 2", "country": "FR", "city": "Vélizy"},
    ]


@st.cache_data
def get_mall_kpis(mall_id: int | None = None):
    """Get KPIs for a specific mall or all malls.

    Args:
        mall_id: Optional mall ID. If None, returns aggregate KPIs.

    Returns:
        dict: Dictionary containing KPI values.
    """
    # TODO: Replace with actual KPI calculations from fact_malls_v1.csv
    # Example structure:
    return {
        "footfall": 150_000,
        "footfall_delta": 5.2,  # % change
        "avg_dwell_time": 65,  # minutes
        "dwell_time_delta": -2.1,
        "conversion_rate": 32.5,  # %
        "conversion_delta": 1.8,
        "revenue": 2_500_000,  # EUR
        "revenue_delta": 8.3,
    }


@st.cache_data
def get_top_stores(mall_id: int, metric: str = "footfall", limit: int = 5):
    """Get top performing stores for a mall.

    Args:
        mall_id: Mall ID to filter stores.
        metric: Metric to rank by (footfall, revenue, dwell_time, etc.)
        limit: Number of top stores to return.

    Returns:
        list: List of store dictionaries with rankings.
    """
    # TODO: Replace with actual data from fact_stores_v1.csv
    # Example structure:
    return [
        {"rank": 1, "name": "Zara", "value": 25_000, "delta": 12.5},
        {"rank": 2, "name": "H&M", "value": 22_000, "delta": 8.2},
        {"rank": 3, "name": "Nike", "value": 18_500, "delta": -2.1},
        {"rank": 4, "name": "Apple Store", "value": 15_000, "delta": 15.8},
        {"rank": 5, "name": "Sephora", "value": 14_200, "delta": 5.4},
    ]


@st.cache_data
def get_mall_trends(mall_id: int, period: str = "30d"):
    """Get trend data for charts.

    Args:
        mall_id: Mall ID to get trends for.
        period: Time period (7d, 30d, 90d, 1y).

    Returns:
        DataFrame: Time series data for plotting.
    """
    # TODO: Replace with actual trend data
    # Return a DataFrame with date, footfall, revenue, etc.
    import numpy as np
    import pandas as pd

    dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "footfall": np.random.randint(10000, 20000, 30),
            "revenue": np.random.randint(50000, 150000, 30),
        }
    )


# =============================================================================
# UI COMPONENTS
# =============================================================================


def render_kpi_card(label: str, value: str, delta: float | None = None):
    """Render a styled KPI metric card.

    Args:
        label: KPI label text.
        value: Formatted KPI value.
        delta: Optional percentage change.
    """
    delta_str = None
    if delta is not None:
        delta_str = f"{delta:+.1f}%"
    st.metric(label=label, value=value, delta=delta_str)


def render_mall_card(mall: dict):
    """Render a clickable mall card for the main dashboard.

    Args:
        mall: Mall dictionary with id, name, country, city.
    """
    kpis = get_mall_kpis(mall["id"])

    with st.container():
        st.markdown(
            f"""
            <div class="mall-card">
                <h3>{mall["name"]}</h3>
                <p style="color: {URW_COLORS["text_muted"]};">
                    {mall["city"]}, {mall["country"]}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            render_kpi_card("Footfall", f"{kpis['footfall']:,}", kpis["footfall_delta"])
        with col2:
            render_kpi_card(
                "Avg. Dwell", f"{kpis['avg_dwell_time']}min", kpis["dwell_time_delta"]
            )

        if st.button("View Details", key=f"btn_{mall['id']}", use_container_width=True):
            st.session_state.selected_mall = mall["id"]
            st.session_state.page = "mall_detail"
            st.rerun()


def render_store_ranking(stores: list, metric_name: str):
    """Render a ranking of top stores.

    Args:
        stores: List of store dictionaries with rank, name, value, delta.
        metric_name: Name of the metric being displayed.
    """
    st.subheader(f"Top Stores by {metric_name}")

    for store in stores:
        delta_color = (
            URW_COLORS["success"] if store["delta"] >= 0 else URW_COLORS["danger"]
        )
        delta_icon = "" if store["delta"] >= 0 else ""

        st.markdown(
            f"""
            <div class="store-rank">
                <span class="rank-number">#{store["rank"]}</span>
                <div style="flex-grow: 1;">
                    <div style="color: {URW_COLORS["text"]}; font-weight: 500;">
                        {store["name"]}
                    </div>
                    <div style="color: {URW_COLORS["text_muted"]}; font-size: 0.85rem;">
                        {store["value"]:,} visitors
                    </div>
                </div>
                <div style="color: {delta_color}; font-weight: 500;">
                    {delta_icon} {store["delta"]:+.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================================
# PAGES
# =============================================================================


LOGO_PATH = "assets/URW.PA.png"


def page_main_dashboard():
    """Main dashboard showing all malls overview."""
    # Header with URW branding
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image(LOGO_PATH, width=80)
    with col_title:
        st.markdown(
            """
            <h1 style="margin: 0; padding-top: 10px;">Mall Analytics</h1>
            <p class="subtitle" style="margin: 0;">
                Real-time performance insights across your portfolio
            </p>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<hr style="border-color: {URW_COLORS["accent"]}; margin: 20px 0;">',
        unsafe_allow_html=True,
    )

    # Portfolio-level KPIs
    st.subheader("Portfolio Overview")
    kpis = get_mall_kpis()  # Aggregate KPIs

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(
            "Total Footfall", f"{kpis['footfall']:,}", kpis["footfall_delta"]
        )
    with col2:
        render_kpi_card(
            "Avg. Dwell Time", f"{kpis['avg_dwell_time']}min", kpis["dwell_time_delta"]
        )
    with col3:
        render_kpi_card(
            "Conversion Rate", f"{kpis['conversion_rate']}%", kpis["conversion_delta"]
        )
    with col4:
        render_kpi_card("Revenue", f"${kpis['revenue']:,}", kpis["revenue_delta"])

    st.divider()

    # Mall cards
    st.subheader("Select a Mall")
    malls = load_malls()

    cols = st.columns(len(malls))
    for idx, mall in enumerate(malls):
        with cols[idx]:
            render_mall_card(mall)


def page_mall_detail():
    """Detailed view for a specific mall."""
    mall_id = st.session_state.get("selected_mall")
    malls = load_malls()
    mall = next((m for m in malls if m["id"] == mall_id), None)

    if not mall:
        st.error("Mall not found")
        return

    # Back button
    if st.button("Back to Dashboard"):
        st.session_state.page = "main"
        st.rerun()

    # Mall header
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image(LOGO_PATH, width=80)
    with col_title:
        st.markdown(
            f"""
            <h1 style="margin: 0; padding-top: 10px;">{mall["name"]}</h1>
            <p class="subtitle" style="margin: 0;">{mall["city"]}, {mall["country"]}</p>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<hr style="border-color: {URW_COLORS["accent"]}; margin: 20px 0;">',
        unsafe_allow_html=True,
    )

    # Mall KPIs
    st.subheader("Key Performance Indicators")
    kpis = get_mall_kpis(mall_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("Footfall", f"{kpis['footfall']:,}", kpis["footfall_delta"])
    with col2:
        render_kpi_card(
            "Avg. Dwell Time", f"{kpis['avg_dwell_time']}min", kpis["dwell_time_delta"]
        )
    with col3:
        render_kpi_card(
            "Conversion Rate", f"{kpis['conversion_rate']}%", kpis["conversion_delta"]
        )
    with col4:
        render_kpi_card("Revenue", f"${kpis['revenue']:,}", kpis["revenue_delta"])

    st.divider()

    # Trend charts and top stores
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Footfall Trends")
        period = st.selectbox(
            "Time Period",
            options=["7d", "30d", "90d", "1y"],
            index=1,
            format_func=lambda x: {
                "7d": "Last 7 Days",
                "30d": "Last 30 Days",
                "90d": "Last 90 Days",
                "1y": "Last Year",
            }[x],
        )
        trend_data = get_mall_trends(mall_id, period)
        st.line_chart(
            trend_data.set_index("date")["footfall"], use_container_width=True
        )

    with col_right:
        metric = st.selectbox(
            "Rank Stores By",
            options=["footfall", "revenue", "dwell_time"],
            format_func=lambda x: {
                "footfall": "Footfall",
                "revenue": "Revenue",
                "dwell_time": "Dwell Time",
            }[x],
        )
        stores = get_top_stores(mall_id, metric=metric)
        render_store_ranking(stores, metric.replace("_", " ").title())


# =============================================================================
# MAIN APP
# =============================================================================


def main():
    """Main entry point for the Streamlit app."""
    st.set_page_config(
        page_title="URW Mall Analytics",
        page_icon="",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    apply_urw_styling()

    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "main"
    if "selected_mall" not in st.session_state:
        st.session_state.selected_mall = None
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False

    # Inject JS to collapse sidebar if requested
    if st.session_state.sidebar_collapsed:
        st.markdown(
            """
            <script>
                var sidebar = window.parent.document.querySelector(
                    '[data-testid="stSidebar"]'
                );
                if (sidebar) {
                    var closeBtn = sidebar.querySelector('button[kind="header"]');
                    if (closeBtn) closeBtn.click();
                }
            </script>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.sidebar_collapsed = False

    # Sidebar navigation
    with st.sidebar:
        # Collapse button at top
        if st.button("Close Sidebar", use_container_width=True, key="collapse_sidebar"):
            st.session_state.sidebar_collapsed = True
            st.rerun()

        # URW Logo
        st.image(LOGO_PATH, use_container_width=True)
        st.markdown("---")

        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = "main"
            st.session_state.selected_mall = None
            st.rerun()

        st.markdown("---")
        st.markdown(
            f"""
            <p style="color: {URW_COLORS["text_muted"]}; font-size: 0.75rem;
                      text-align: center;">
                URW Data Challenge<br>
                XHEC DSB 2025
            </p>
            """,
            unsafe_allow_html=True,
        )

    # Route to appropriate page
    if st.session_state.page == "mall_detail" and st.session_state.selected_mall:
        page_mall_detail()
    else:
        page_main_dashboard()


if __name__ == "__main__":
    main()
