"""Functions used to load data for the Streamlit app."""

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
