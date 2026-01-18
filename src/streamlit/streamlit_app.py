"""URW Mall Analytics Dashboard.

Main entry point for the Streamlit app.
"""

from src.streamlit.looks import URW_COLORS, apply_urw_styling
from src.streamlit.pages import page_main_dashboard, page_mall_detail
import streamlit as st

LOGO_PATH = "assets/URW.PA.png"


def render_sidebar():
    """Render the sidebar with navigation and weight controls."""
    with st.sidebar:
        # URW Logo
        st.image(LOGO_PATH, use_container_width=True)
        st.markdown("---")

        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = "main"
            st.session_state.selected_mall = None
            st.rerun()

        st.markdown("---")

        # Composite Score Weights
        st.markdown("#### Composite Score Weights")
        st.caption("Select 2 metrics to adjust. The third auto-completes to 100%.")

        # Initialize weights in session state
        if "weight_sales" not in st.session_state:
            st.session_state.weight_sales = 0.4
        if "weight_dwell" not in st.session_state:
            st.session_state.weight_dwell = 0.3
        if "weight_sri" not in st.session_state:
            st.session_state.weight_sri = 0.3
        if "adjust_sales" not in st.session_state:
            st.session_state.adjust_sales = True
        if "adjust_dwell" not in st.session_state:
            st.session_state.adjust_dwell = True
        if "adjust_sri" not in st.session_state:
            st.session_state.adjust_sri = False

        # Checkboxes for selecting which metrics to adjust
        col_cb1, col_cb2, col_cb3 = st.columns(3)
        with col_cb1:
            adjust_sales = st.checkbox(
                "Sales", value=st.session_state.adjust_sales, key="cb_sales"
            )
        with col_cb2:
            adjust_dwell = st.checkbox(
                "Dwell", value=st.session_state.adjust_dwell, key="cb_dwell"
            )
        with col_cb3:
            adjust_sri = st.checkbox(
                "SRI", value=st.session_state.adjust_sri, key="cb_sri"
            )

        # Enforce exactly 2 checkboxes selected
        selected = [adjust_sales, adjust_dwell, adjust_sri]
        num_selected = sum(selected)

        if num_selected != 2:
            # Revert to previous state if invalid
            adjust_sales = st.session_state.adjust_sales
            adjust_dwell = st.session_state.adjust_dwell
            adjust_sri = st.session_state.adjust_sri
            st.warning("Please select exactly 2 metrics to adjust.")
        else:
            st.session_state.adjust_sales = adjust_sales
            st.session_state.adjust_dwell = adjust_dwell
            st.session_state.adjust_sri = adjust_sri

        # Get current weights
        weight_sales = st.session_state.weight_sales
        weight_dwell = st.session_state.weight_dwell
        weight_sri = st.session_state.weight_sri

        # Display sliders for selected metrics (all 0 to 1)
        if adjust_sales:
            weight_sales = st.slider(
                "Sales Weight",
                min_value=0.0,
                max_value=1.0,
                value=weight_sales,
                step=0.05,
                key="slider_sales",
            )
            st.session_state.weight_sales = weight_sales

        if adjust_dwell:
            weight_dwell = st.slider(
                "Dwell Time Weight",
                min_value=0.0,
                max_value=1.0,
                value=weight_dwell,
                step=0.05,
                key="slider_dwell",
            )
            st.session_state.weight_dwell = weight_dwell

        if adjust_sri:
            weight_sri = st.slider(
                "SRI Weight",
                min_value=0.0,
                max_value=1.0,
                value=weight_sri,
                step=0.05,
                key="slider_sri",
            )
            st.session_state.weight_sri = weight_sri

        # Compute sum of selected sliders
        selected_sum = 0.0
        if adjust_sales:
            selected_sum += weight_sales
        if adjust_dwell:
            selected_sum += weight_dwell
        if adjust_sri:
            selected_sum += weight_sri

        # Check if sum exceeds 1
        sum_exceeds = selected_sum > 1.0

        if sum_exceeds:
            st.warning(f"Sum of selected weights ({selected_sum:.0%}) exceeds 100%.")

        # Compute the auto-calculated weight (clamped to 0 if sum exceeds 1)
        if not adjust_sales:
            weight_sales = max(0.0, 1.0 - weight_dwell - weight_sri)
            st.session_state.weight_sales = weight_sales
        elif not adjust_dwell:
            weight_dwell = max(0.0, 1.0 - weight_sales - weight_sri)
            st.session_state.weight_dwell = weight_dwell
        elif not adjust_sri:
            weight_sri = max(0.0, 1.0 - weight_sales - weight_dwell)
            st.session_state.weight_sri = weight_sri

        # Display final weights summary
        st.markdown(
            f"**Sales:** {weight_sales:.0%}" + (" *(auto)*" if not adjust_sales else "")
        )
        st.markdown(
            f"**Dwell:** {weight_dwell:.0%}" + (" *(auto)*" if not adjust_dwell else "")
        )
        st.markdown(
            f"**SRI:** {weight_sri:.0%}" + (" *(auto)*" if not adjust_sri else "")
        )

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

    # Render sidebar
    render_sidebar()

    # Route to appropriate page
    if st.session_state.page == "mall_detail" and st.session_state.selected_mall:
        page_mall_detail()
    else:
        page_main_dashboard()


if __name__ == "__main__":
    main()
