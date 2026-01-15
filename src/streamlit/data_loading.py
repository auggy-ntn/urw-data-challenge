"""Functions used to load data for the Streamlit app."""

import joblib
import pandas as pd

from constants import column_names as col
from constants import paths as pth
import constants.constants as cst
from src.utils.logger import logger
import streamlit as st


@st.cache_data
def load_malls():
    """Load mall dimension data.

    Returns:
        list: List of mall dictionaries with id, name, country, etc.
    """
    try:
        dim_malls = pd.read_csv(pth.INTERMEDIATE_DIM_MALLS, **cst.CSV_PARAMS)
        dim_malls = dim_malls.rename(columns={col.MALL_NAME: "name"})
        # Fill NaN mall names with "Mall {id}"
        dim_malls["name"] = dim_malls.apply(
            lambda row: row["name"] if pd.notna(row["name"]) else f"Mall {row[col.ID]}",
            axis=1,
        )
        malls = dim_malls[[col.ID, col.COUNTRY, "name"]].to_dict(orient="records")
        return malls
    except Exception as e:
        logger.error(f"Error loading mall data: {e}")
        return []


@st.cache_data
def get_mall_kpis(mall_id: int | None = None):
    """Get KPIs for a specific mall or all malls.

    Args:
        mall_id: Optional mall ID. If None, returns aggregate KPIs.

    Returns:
        dict: Dictionary containing KPI values.
    """
    try:
        mall_kpis = pd.read_csv(pth.ENRICHED_MALL_KPIS, index_col=0)  # Index is mall_id
    except Exception as e:
        logger.error(f"Error loading mall KPIs: {e}")
        return {}

    # If mall_id is None, return aggregate KPIs
    if mall_id is None:
        return mall_kpis.mean(numeric_only=True).to_dict()

    # Return KPIs for the specified mall
    else:
        return mall_kpis.loc[mall_id].to_dict()


@st.cache_data
def get_top_stores(mall_id: int, metric: str = "footfall", limit: int = 5):
    """Get top performing stores for a mall.

    Args:
        mall_id: Mall ID to filter stores.
        metric: Metric to rank by (footfall, revenue, dwell_time).
        limit: Number of top stores to return.

    Returns:
        list: List of store dictionaries with rank, name, value, delta.
    """
    # Map UI metric names to actual column names
    metric_mapping = {
        "footfall": col.DAILY_PEOPLE_IN_LAST_XM,
        "revenue": col.SALES_R12M,
        "dwell_time": col.AVG_DWELL_TIME_LAST_XM,
    }
    delta_mapping = {
        "footfall": col.PCT_CHANGE_PEOPLE_IN,
        "revenue": None,
        "dwell_time": "pct_change_average_dwell_time",
    }

    try:
        store_kpis = pd.read_csv(pth.ENRICHED_STORE_KPIS, index_col=0)
    except Exception as e:
        logger.error(f"Error loading store KPIs: {e}")
        return []

    sort_col = metric_mapping.get(metric, col.DAILY_PEOPLE_IN_LAST_XM)
    delta_col = delta_mapping.get(metric)

    # Filter stores for this mall
    mall_stores = store_kpis[store_kpis[col.MALL_ID] == mall_id].copy()

    if mall_stores.empty:
        logger.warning(f"No stores found for mall_id={mall_id}")
        return []

    top_stores = mall_stores.sort_values(by=sort_col, ascending=False).head(limit)

    # Format output for UI
    result = []
    for rank, (store_code, row) in enumerate(top_stores.iterrows(), start=1):
        value = int(row[sort_col]) if pd.notna(row[sort_col]) else 0
        delta = 0
        if delta_col and pd.notna(row.get(delta_col)):
            delta = row[delta_col]

        # Get retailer name (store_name or fallback to retailer_code)
        store_name = row.get(col.STORE_NAME)
        retailer_code = row.get(col.RETAILER_CODE)
        if pd.notna(store_name) and store_name:
            retailer_name = store_name
        elif pd.notna(retailer_code) and retailer_code:
            retailer_name = retailer_code
        else:
            retailer_name = f"Store {store_code}"

        # Get category
        category = row.get(col.CAT_HIGH)
        category = category if pd.notna(category) else "Unknown"

        result.append(
            {
                "rank": rank,
                "name": retailer_name,
                "category": category,
                "value": value,
                "delta": delta,
            }
        )
    return result


# =============================================================================
# SWAP PREDICTOR DATA LOADING
# =============================================================================


@st.cache_resource
def load_models_and_encoders():
    """Load trained models and encoders for swap prediction.

    Returns:
        tuple: (models dict, encoders dict) or (None, None) if loading fails.
    """
    try:
        # Load models for sales_per_sqm and dwell_time
        models = {}
        encoders = {}

        for target in [col.TARGET_SALES_PER_SQM, col.TARGET_DWELL_TIME]:
            model_path = pth.MODELS_DIR / f"{target}_model.joblib"
            encoder_path = pth.MODELS_DIR / f"{target}_encoders.joblib"

            if model_path.exists() and encoder_path.exists():
                models[target] = joblib.load(model_path)
                encoders[target] = joblib.load(encoder_path)
            else:
                logger.warning(f"Model files not found for {target}")
                return None, None

        # Use sales_per_sqm encoders for the swap predictor (they should be the same)
        return models, encoders[col.TARGET_SALES_PER_SQM]
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        return None, None


@st.cache_data
def load_swap_predictor_data():
    """Load all data needed for swap prediction.

    Returns:
        dict: Dictionary with all required DataFrames, or None if loading fails.
    """
    try:
        # Load raw data
        dim_blocks = pd.read_csv(pth.INTERMEDIATE_DIM_BLOCKS, **cst.CSV_PARAMS)
        store_metrics = pd.read_csv(
            pth.ENRICHED_STORE_METRICS, index_col=col.STORE_CODE
        )
        store_financials = pd.read_csv(
            pth.INTERMEDIATE_STORE_FINANCIALS, **cst.CSV_PARAMS
        )
        cross_visits = pd.read_csv(pth.INTERMEDIATE_CROSS_VISITS, **cst.CSV_PARAMS)
        affinity_matrix = pd.read_csv(
            pth.ENRICHED_CATEGORY_AFFINITIES, **cst.CSV_PARAMS
        )
        sri_scores = pd.read_csv(pth.INTERMEDIATE_FACT_SRI_SCORES, **cst.CSV_PARAMS)
        category_sri_avg = pd.read_csv(pth.ENRICHED_CATEGORY_SRI_AVG, **cst.CSV_PARAMS)

        # Compute target values (sales_per_sqm and dwell_time)
        # Get GLA from dim_blocks (deduplicated by store_code)
        store_gla = dim_blocks.drop_duplicates(subset=[col.STORE_CODE]).set_index(
            col.STORE_CODE
        )[col.GLA]

        # Get sales from store_financials
        store_sales = store_financials.set_index(col.STORE_CODE)[col.SALES_R12M]

        # Compute sales_per_sqm
        common_stores = store_gla.index.intersection(store_sales.index)
        sales_per_sqm = store_sales.loc[common_stores] / store_gla.loc[common_stores]

        # Build store_performance DataFrame with target columns
        store_performance = pd.DataFrame(index=store_metrics.index)
        store_performance[col.TARGET_SALES_PER_SQM] = sales_per_sqm
        store_performance[col.TARGET_DWELL_TIME] = store_metrics[
            col.MODEL_STORE_AVG_DWELL_TIME
        ]

        # Load mall means for normalization
        if pth.MALL_MEANS.exists():
            mall_means_df = pd.read_csv(pth.MALL_MEANS)
            mall_means = {}
            for target in [col.TARGET_SALES_PER_SQM, col.TARGET_DWELL_TIME]:
                target_rows = mall_means_df[mall_means_df["target"] == target]
                mall_means[target] = dict(
                    zip(
                        target_rows["mall_id"],
                        target_rows["mean_value"],
                        strict=False,
                    )
                )

            # Normalize by mall means
            store_mall_ids = dim_blocks.drop_duplicates(
                subset=[col.STORE_CODE]
            ).set_index(col.STORE_CODE)[col.MALL_ID]

            for target in [col.TARGET_SALES_PER_SQM, col.TARGET_DWELL_TIME]:
                mall_mean_series = store_mall_ids.map(mall_means[target])
                valid_idx = store_performance.index.intersection(mall_mean_series.index)
                store_performance.loc[valid_idx, target] = (
                    store_performance.loc[valid_idx, target]
                    / mall_mean_series.loc[valid_idx]
                )

        data = {
            "dim_blocks": dim_blocks,
            "store_metrics": store_metrics,
            "store_performance": store_performance,
            "cross_visits": cross_visits,
            "affinity_matrix": affinity_matrix,
            "sri_scores": sri_scores,
            "category_sri_avg": category_sri_avg,
            "mall_means": mall_means,
        }
        return data
    except Exception as e:
        logger.error(f"Error loading swap predictor data: {e}")
        return None


@st.cache_data
def get_mall_stores_for_swap(mall_id: int):
    """Get stores in a mall for the swap dropdown.

    Args:
        mall_id: Mall ID to filter stores.

    Returns:
        list: List of dicts with store_code, name, category.
    """
    try:
        dim_blocks = pd.read_csv(pth.INTERMEDIATE_DIM_BLOCKS, **cst.CSV_PARAMS)
        mall_stores = dim_blocks[dim_blocks[col.MALL_ID] == mall_id].drop_duplicates(
            subset=[col.STORE_CODE]
        )

        stores = []
        for _, row in mall_stores.iterrows():
            store_name = row.get(col.STORE_NAME)
            retailer_code = row.get(col.RETAILER_CODE)

            if pd.notna(store_name) and store_name:
                display_name = store_name
            elif pd.notna(retailer_code) and retailer_code:
                display_name = retailer_code
            else:
                display_name = f"Store {row[col.STORE_CODE]}"

            category = row.get(col.CAT_HIGH, "Unknown")
            category = category if pd.notna(category) else "Unknown"

            stores.append(
                {
                    "store_code": row[col.STORE_CODE],
                    "name": display_name,
                    "category": category,
                }
            )

        return sorted(stores, key=lambda x: x["name"])
    except Exception as e:
        logger.error(f"Error loading mall stores: {e}")
        return []


@st.cache_data
def get_all_categories():
    """Get all unique store categories.

    Returns:
        list: Sorted list of category names.
    """
    try:
        dim_blocks = pd.read_csv(pth.INTERMEDIATE_DIM_BLOCKS, **cst.CSV_PARAMS)
        categories = dim_blocks[col.CAT_HIGH].dropna().unique().tolist()
        return sorted(categories)
    except Exception as e:
        logger.error(f"Error loading categories: {e}")
        return []
