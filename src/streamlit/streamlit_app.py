"""URW Mall Analytics Dashboard.

Streamlit app for visualizing mall and store KPIs.
"""

from constants import column_names as col
from constants import constants as cst
from src.streamlit.data_loading import (
    get_all_categories,
    get_mall_kpis,
    get_mall_stores_for_swap,
    get_top_stores,
    load_malls,
    load_models_and_encoders,
    load_swap_predictor_data,
)
from src.streamlit.looks import URW_COLORS, apply_urw_styling
from src.utils.swap_predictor import predict_swap_impact
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
                    Country: {mall["country"]}
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
        "OCR": "",
    }
    unit = unit_mapping.get(metric_name, "")

    for store in stores:
        delta = store.get("delta")

        # Format value based on metric
        value = store.get("value")
        if value is None:
            value_str = "No data"
        elif metric_name == "Revenue":
            value_str = f"€{value:,}"
        elif metric_name == "Dwell Time":
            value_str = f"{value} min"
        elif metric_name == "OCR":
            value_str = f"{value:.2f}"
        else:
            value_str = f"{value:,} {unit}"

        # Format delta display as bubble with label
        delta_label = (
            f'<span style="color: {URW_COLORS["text_muted"]}; font-size: 0.75rem; '
            f'margin-right: 8px;">Change in the last {cst.WINDOW_SIZE} month(s)</span>'
        )
        if delta is None:
            # No delta available (e.g., revenue, OCR) - grey bubble
            delta_str = (
                f"{delta_label}"
                f'<span style="background-color: {URW_COLORS["text_muted"]}20; '
                f"color: {URW_COLORS['text_muted']}; "
                f"padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; "
                f'font-weight: 500;">No data</span>'
            )
        elif delta != 0:
            delta_color = URW_COLORS["success"] if delta >= 0 else URW_COLORS["danger"]
            delta_str = (
                f"{delta_label}"
                f'<span style="background-color: {delta_color}20; '
                f"color: {delta_color}; "
                f"padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; "
                f'font-weight: 500;">{delta:+.1f}%</span>'
            )
        else:
            # Zero delta - grey bubble
            delta_str = (
                f"{delta_label}"
                f'<span style="background-color: {URW_COLORS["text_muted"]}20; '
                f"color: {URW_COLORS['text_muted']}; "
                f"padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; "
                f'font-weight: 500;">0.0%</span>'
            )

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
    st.subheader("Overall View")
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


def render_swap_predictor(mall_id: int):
    """Render the swap predictor section for a mall.

    Args:
        mall_id: The mall ID to predict swaps for.
    """
    st.subheader("Store Swap Predictor")
    st.markdown(
        f"""
        <p style="color: {URW_COLORS["text"]};">
            Predict how swapping a store to a different category would impact mall
            performance.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Load models and data
    models, encoders = load_models_and_encoders()
    swap_data = load_swap_predictor_data()

    if models is None or swap_data is None:
        st.warning("Swap predictor models not available. Run model training first.")
        return

    # Get stores and categories for dropdowns
    mall_stores = get_mall_stores_for_swap(mall_id)
    categories = get_all_categories()

    if not mall_stores:
        st.info("No stores available for this mall")
        return

    # Store and category selection
    col1, col2 = st.columns(2)

    with col1:
        store_options = {
            s["store_code"]: f"{s['name']} ({s['category']})" for s in mall_stores
        }
        selected_store = st.selectbox(
            "Select Store to Swap",
            options=list(store_options.keys()),
            format_func=lambda x: store_options[x],
            key="swap_store_select",
        )

    # Get current category of selected store
    current_store = next(s for s in mall_stores if s["store_code"] == selected_store)
    current_category = current_store["category"]

    with col2:
        # Filter out current category from options
        available_categories = [c for c in categories if c != current_category]
        new_category = st.selectbox(
            "Swap to Category",
            options=available_categories,
            key="swap_category_select",
        )

    # Predict button
    if st.button("Predict Swap Impact", type="primary", use_container_width=True):
        with st.spinner("Calculating swap impact..."):
            try:
                # Prepare data for prediction
                dim_blocks = swap_data["dim_blocks"]
                store_metrics = swap_data["store_metrics"]
                store_performance = swap_data["store_performance"]
                cross_visits = swap_data["cross_visits"]
                affinity_matrix = swap_data["affinity_matrix"]
                sri_scores = swap_data["sri_scores"]
                category_sri_avg = swap_data["category_sri_avg"]

                # Check if store performance data is available
                if store_performance.empty:
                    st.error("Store performance data not available")
                    return

                # Build SRI series
                current_sri = sri_scores.set_index(col.STORE_CODE)[col.SRI_SCORE]

                # Build category SRI average series
                cat_sri_series = category_sri_avg.set_index(col.CAT_HIGH)[col.SRI_SCORE]

                # Run prediction
                result = predict_swap_impact(
                    store_to_swap=selected_store,
                    new_category=new_category,
                    models=models,
                    encoders=encoders,
                    dim_blocks=dim_blocks,
                    store_total=store_metrics,
                    cross_visits=cross_visits,
                    affinity_matrix=affinity_matrix,
                    current_store_performance=store_performance,
                    current_store_sri=current_sri,
                    category_sri_avg=cat_sri_series,
                )

                # Store result in session state to display
                st.session_state.swap_result = result

            except Exception as e:
                st.error(f"Error predicting swap: {e}")
                return

    # Display results if available
    if "swap_result" in st.session_state:
        result = st.session_state.swap_result
        mall_means = swap_data.get("mall_means")
        render_swap_results(result, mall_means)


def render_swap_results(result: dict, mall_means: dict | None = None):
    """Render the swap prediction results.

    Args:
        result: Dictionary with swap prediction results.
        mall_means: Dictionary with mall means for denormalization.
    """
    st.markdown("---")
    st.markdown("### Prediction Results")

    swapped = result["swapped_store"]
    improvement = result["improvement"]
    mall_id = result["current_mall_metrics"]["mall_id"]

    # Denormalize metrics if mall_means is available
    cur_sales = result["current_mall_metrics"]["avg_sales_per_sqm"]
    cur_dwell = result["current_mall_metrics"]["avg_dwell_time"]
    pred_sales = result["predicted_mall_metrics"]["avg_sales_per_sqm"]
    pred_dwell = result["predicted_mall_metrics"]["avg_dwell_time"]

    new_store_sales = result["new_store_predictions"]["sales_per_sqm"]
    new_store_dwell = result["new_store_predictions"]["dwell_time"]

    if mall_means:
        # Get means for this mall
        sales_mean = mall_means.get(col.TARGET_SALES_PER_SQM, {}).get(mall_id, 1.0)
        dwell_mean = mall_means.get(col.TARGET_DWELL_TIME, {}).get(mall_id, 1.0)

        cur_sales *= sales_mean
        cur_dwell *= dwell_mean
        pred_sales *= sales_mean
        pred_dwell *= dwell_mean
        new_store_sales *= sales_mean
        new_store_dwell *= dwell_mean

    # Swap summary
    gla_pct = swapped["gla_share"] * 100
    st.markdown(
        f"""
        **Swap Summary:** {swapped["old_category"]} → **{swapped["new_category"]}**
        (Store GLA: {swapped["gla"]:,.0f} sqm, {gla_pct:.1f}% of mall)
        """
    )

    # Improvement metrics
    composite_change = improvement["composite_pct"]
    if composite_change >= 0:
        composite_color = URW_COLORS["success"]
    else:
        composite_color = URW_COLORS["danger"]

    st.markdown(
        f"""
        <div style="background-color: {URW_COLORS["secondary"]}; padding: 20px;
                    border-radius: 10px; margin: 10px 0;">
            <h4 style="margin: 0 0 15px 0;">Mall Composite Score Impact</h4>
            <div style="font-size: 2rem; font-weight: bold; color: {composite_color};">
                {composite_change:+.2f}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Projected Mall Metrics
    st.markdown("#### Projected Mall Impact")
    col1, col2, col3 = st.columns(3)

    # Calculate Total Revenue Impact
    # 1. Get current total mall revenue (in M€)
    kpis = get_mall_kpis(mall_id)
    current_mall_revenue_m = kpis.get(col.TOTAL_MALL_SALES, 0)
    current_mall_revenue = current_mall_revenue_m * 1_000_000

    # 2. Calculate delta revenue from store swap
    # sales_per_sqm is in Euros
    # current_store_sales = old_sales_sqm * gla
    # new_store_sales = new_sales_sqm * gla
    swapped_gla = swapped["gla"]

    # Get normalized metrics
    metrics = swapped.get("metrics", {})
    old_sales_norm = metrics.get("sales_per_sqm", 0.0)
    new_sales_norm = result["new_store_predictions"]["sales_per_sqm"]

    # Denormalize
    sales_mean = 1.0
    if mall_means:
        sales_mean = mall_means.get(col.TARGET_SALES_PER_SQM, {}).get(mall_id, 1.0)

    old_sales_sqm = old_sales_norm * sales_mean
    new_sales_sqm = new_sales_norm * sales_mean

    delta_revenue = (new_sales_sqm - old_sales_sqm) * swapped_gla

    new_mall_revenue = current_mall_revenue + delta_revenue
    new_mall_revenue_m = new_mall_revenue / 1_000_000

    revenue_pct_change = (
        (delta_revenue / current_mall_revenue) * 100 if current_mall_revenue else 0
    )

    with col1:
        st.metric(
            "Projected Total Revenue",
            f"€{new_mall_revenue_m:,.1f}M",
            f"{revenue_pct_change:+.2f}%",
        )

    # Calculate Projected Mall Dwell Time
    current_mall_dwell = kpis.get(col.AVG_DWELL_TIME_LAST_XM, 0)
    dwell_pct_change = improvement["dwell_pct"]
    new_mall_dwell = current_mall_dwell * (1 + dwell_pct_change / 100)

    with col2:
        st.metric(
            "Projected Mall Dwell Time",
            f"{new_mall_dwell:.1f} min",
            f"{dwell_pct_change:+.1f}%",
        )

    with col3:
        sri_change = improvement["sri_pct"]
        st.metric(
            "SRI Score (Weighted)",
            f"{result['predicted_mall_metrics']['avg_sri_gla_weighted']:.1f}",
            f"{sri_change:+.1f}%",
        )


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
