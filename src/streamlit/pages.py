"""Page definitions for the Streamlit dashboard."""

import math

from constants import column_names as col
from src.streamlit.components import (
    render_kpi_card,
    render_mall_card,
    render_retail_mix_chart,
    render_store_ranking,
    render_swap_predictor,
    render_trend_section,
)
from src.streamlit.data_loading import (
    get_category_forecasts,
    get_category_trends,
    get_mall_kpis,
    get_top_stores,
    load_malls,
)
from src.streamlit.looks import URW_COLORS
import streamlit as st

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
    st.subheader("Overall View")
    kpis = get_mall_kpis()  # Aggregate KPIs

    if kpis:

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

    # Global Category Trends
    with st.spinner("Loading trend data..."):
        historical_trends = get_category_trends(mall_id=None)  # Global
        forecast_trends = get_category_forecasts(mall_id=None)  # Global

    if not historical_trends.empty:
        render_trend_section(
            historical_df=historical_trends,
            forecast_df=forecast_trends,
            historical_horizon="1_month",
            forecast_horizon="1_month",
            title="Category Trends (All Malls)",
            columns=6,
        )

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
            <p class="subtitle" style="margin: 10px;">Country: {mall["country"]}</p>
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

        def is_valid(val):
            return val is not None and not (isinstance(val, float) and math.isnan(val))

        footfall_raw = kpis.get(col.DAILY_PEOPLE_IN_LAST_XM)
        dwell_raw = kpis.get(col.AVG_DWELL_TIME_LAST_XM)
        revenue_raw = kpis.get(col.TOTAL_MALL_SALES)
        sri_raw = kpis.get(col.AVG_MALL_SRI)

        footfall_str = f"{int(footfall_raw):,}" if is_valid(footfall_raw) else "No data"
        dwell_str = f"{dwell_raw:.0f}min" if is_valid(dwell_raw) else "No data"
        revenue_str = f"€{revenue_raw:.1f}M" if is_valid(revenue_raw) else "No data"
        sri_str = f"{sri_raw:.1f}" if is_valid(sri_raw) else "No data"

        col1, col2, col3, col4 = st.columns(4)
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
        with col4:
            render_kpi_card("Avg. SRI Score", sri_str, None)

    st.divider()

    # Mall-specific Category Trends
    with st.spinner("Loading trend data..."):
        historical_trends = get_category_trends(mall_id=mall_id)
        forecast_trends = get_category_forecasts(mall_id=mall_id)

    if not historical_trends.empty:
        render_trend_section(
            historical_df=historical_trends,
            forecast_df=forecast_trends,
            historical_horizon="1_month",
            forecast_horizon="1_month",
            title=f"Category Trends ({mall['name']})",
            columns=6,
            show_sample_warning=True,
        )

    st.divider()

    # Retail Mix Pie Chart
    st.subheader("Retail Mix")
    if kpis:
        render_retail_mix_chart(kpis)

    st.divider()

    # Top stores ranking
    col_title, col_toggle = st.columns([3, 1])
    with col_title:
        st.subheader("Top Stores")
    with col_toggle:
        show_worst = st.checkbox("Show worst", value=False)

    metric = st.selectbox(
        "Rank Stores By",
        options=["footfall", "revenue", "dwell_time", "ocr"],
        format_func=lambda x: {
            "footfall": "Footfall",
            "revenue": "Revenue",
            "dwell_time": "Dwell Time",
            "ocr": "OCR",
        }[x],
    )
    stores = get_top_stores(mall_id, metric=metric, ascending=show_worst)
    metric_display = "OCR" if metric == "ocr" else metric.replace("_", " ").title()
    if stores:
        render_store_ranking(stores, metric_display)
    else:
        st.info("No store data available for this mall")

    st.divider()

    # Swap Predictor Section
    render_swap_predictor(mall_id)
