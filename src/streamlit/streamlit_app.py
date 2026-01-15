"""URW Mall Analytics Dashboard.

Streamlit app for visualizing mall and store KPIs.
"""

from constants import column_names as col
from src.streamlit.data_loading import (
    get_mall_kpis,
    get_top_stores,
    load_malls,
)
from src.streamlit.looks import URW_COLORS, apply_urw_styling
import streamlit as st

# Apply URW styling to the app
apply_urw_styling()


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
    import math

    if delta is not None and not (isinstance(delta, float) and math.isnan(delta)):
        delta_str = f"{delta:+.1f}%"
        st.metric(label=label, value=value, delta=delta_str)
    else:
        # Use delta_color="off" for grey text, keeps alignment consistent
        st.metric(label=label, value=value, delta="No data", delta_color="off")


def render_mall_card(mall: dict):
    """Render a clickable mall card for the main dashboard.

    Args:
        mall: Mall dictionary with id, name, country.
    """
    import math

    kpis = get_mall_kpis(mall["id"])
    if not kpis:
        return

    with st.container():
        st.markdown(
            f"""
            <div class="mall-card">
                <h3>{mall["name"]}</h3>
                <p style="color: {URW_COLORS["text_muted"]};">
                    {mall["country"]}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        footfall_raw = kpis.get(col.DAILY_PEOPLE_IN_LAST_XM)
        dwell_raw = kpis.get(col.AVG_DWELL_TIME_LAST_XM)
        footfall_delta = kpis.get(col.PCT_CHANGE_PEOPLE_IN)
        dwell_delta = kpis.get(col.PCT_CHANGE_AVG_DWELL_TIME)

        # Format values, showing "No data" for NaN
        def is_valid(val):
            return val is not None and not (isinstance(val, float) and math.isnan(val))

        footfall_str = f"{int(footfall_raw):,}" if is_valid(footfall_raw) else "No data"
        dwell_str = f"{dwell_raw:.0f}min" if is_valid(dwell_raw) else "No data"

        col1, col2 = st.columns(2)
        with col1:
            render_kpi_card("Footfall", footfall_str, footfall_delta)
        with col2:
            render_kpi_card("Avg. Dwell", dwell_str, dwell_delta)

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
    # Map metric names to display units
    unit_mapping = {
        "Footfall": "daily visitors",
        "Revenue": "€",
        "Dwell Time": "min",
    }
    unit = unit_mapping.get(metric_name, "")

    for store in stores:
        delta = store.get("delta", 0) or 0
        delta_color = URW_COLORS["success"] if delta >= 0 else URW_COLORS["danger"]

        # Format value based on metric
        value = store.get("value", 0)
        if metric_name == "Revenue":
            value_str = f"€{value:,}"
        elif metric_name == "Dwell Time":
            value_str = f"{value} min"
        else:
            value_str = f"{value:,} {unit}"

        # Format delta display
        if delta != 0:
            delta_str = (
                f'<span style="color: {delta_color}; '
                f'font-weight: 500;">{delta:+.1f}%</span>'
            )
        else:
            delta_str = ""

        category = store.get("category", "")

        st.markdown(
            f"""
            <div class="store-rank">
                <span class="rank-number">#{store["rank"]}</span>
                <div style="flex-grow: 1;">
                    <div style="color: {URW_COLORS["text"]}; font-weight: 500;">
                        {store["name"]}
                    </div>
                    <div style="color: {URW_COLORS["text_muted"]}; font-size: 0.85rem;">
                        {category} · {value_str}
                    </div>
                </div>
                {delta_str}
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
        st.image(LOGO_PATH, use_container_width=True)
    with col_title:
        st.markdown(
            """
            <h1 style="margin: 0; padding-top: 10px;">Mall Analytics</h1>
            <p class="subtitle" style="margin: 0;">
                URW Data Challenge Dashboard
            </p>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<hr style="border-color: {URW_COLORS["accent"]}; margin: 20px 0;">',
        unsafe_allow_html=True,
    )

    # Portfolio-level KPIs
    st.subheader("Malls General Overview")
    kpis = get_mall_kpis()  # Aggregate KPIs

    if kpis:
        import math

        def is_valid(val):
            return val is not None and not (isinstance(val, float) and math.isnan(val))

        footfall_raw = kpis.get(col.DAILY_PEOPLE_IN_LAST_XM)
        dwell_raw = kpis.get(col.AVG_DWELL_TIME_LAST_XM)
        revenue_raw = kpis.get(col.TOTAL_MALL_SALES)

        footfall_str = f"{int(footfall_raw):,}" if is_valid(footfall_raw) else "No data"
        dwell_str = f"{dwell_raw:.0f}min" if is_valid(dwell_raw) else "No data"
        revenue_str = f"€{revenue_raw:.1f}M" if is_valid(revenue_raw) else "No data"

        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card(
                "Avg. Daily Footfall",
                footfall_str,
                kpis.get(col.PCT_CHANGE_PEOPLE_IN),
            )
        with col2:
            render_kpi_card(
                "Avg. Dwell Time",
                dwell_str,
                kpis.get(col.PCT_CHANGE_AVG_DWELL_TIME),
            )
        with col3:
            render_kpi_card("Avg. Revenue (M€)", revenue_str, None)

    st.divider()

    # Mall cards in a grid layout (4 columns)
    st.subheader("Select a Mall")
    malls = load_malls()

    if not malls:
        st.warning("No mall data available")
        return

    # Display malls in rows of 4
    cols_per_row = 4
    for i in range(0, len(malls), cols_per_row):
        row_malls = malls[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, mall in enumerate(row_malls):
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

    # Mall header with back button on the right
    col_logo, col_title, col_back = st.columns([1, 4, 1])
    with col_logo:
        st.image(LOGO_PATH, use_container_width=True)
    with col_title:
        st.markdown(
            f"""
            <h1 style="margin: 0; padding-top: 10px;">{mall["name"]}</h1>
            <p class="subtitle" style="margin: 0;">{mall["country"]}</p>
            """,
            unsafe_allow_html=True,
        )
    with col_back:
        if st.button("← Dashboard", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()
    st.markdown(
        f'<hr style="border-color: {URW_COLORS["accent"]}; margin: 20px 0;">',
        unsafe_allow_html=True,
    )

    # Mall KPIs
    st.subheader("Key Performance Indicators")
    kpis = get_mall_kpis(mall_id)

    if kpis:
        import math

        def is_valid(val):
            return val is not None and not (isinstance(val, float) and math.isnan(val))

        footfall_raw = kpis.get(col.DAILY_PEOPLE_IN_LAST_XM)
        dwell_raw = kpis.get(col.AVG_DWELL_TIME_LAST_XM)
        revenue_raw = kpis.get(col.TOTAL_MALL_SALES)

        footfall_str = f"{int(footfall_raw):,}" if is_valid(footfall_raw) else "No data"
        dwell_str = f"{dwell_raw:.0f}min" if is_valid(dwell_raw) else "No data"
        revenue_str = f"€{revenue_raw:.1f}M" if is_valid(revenue_raw) else "No data"

        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card(
                "Daily Footfall",
                footfall_str,
                kpis.get(col.PCT_CHANGE_PEOPLE_IN),
            )
        with col2:
            render_kpi_card(
                "Avg. Dwell Time",
                dwell_str,
                kpis.get(col.PCT_CHANGE_AVG_DWELL_TIME),
            )
        with col3:
            render_kpi_card("Revenue (M€)", revenue_str, None)

    st.divider()

    # Top stores ranking
    st.subheader("Top Stores")
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
    if stores:
        render_store_ranking(stores, metric.replace("_", " ").title())
    else:
        st.info("No store data available for this mall")


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
    # Sidebar navigation
    with st.sidebar:
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
