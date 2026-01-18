"""Trend calculation utilities for dashboard metrics."""

from datetime import timedelta

import numpy as np
import pandas as pd

from constants import column_names as col
from constants import constants as cst
from constants import paths as pth
from src.utils.logger import logger

# Time horizons for historical growth rate calculation (in days)
TIME_HORIZONS = {
    "2_weeks": 14,
    "1_month": 30,
    "3_months": 90,
    "6_months": 180,
    "9_months": 270,
    "1_year": 365,
}

# Forecast horizons (in days)
FORECAST_HORIZONS = {
    "1_month": 30,
    "2_months": 60,
    "3_months": 90,
}

# Display names for UI
TIME_HORIZON_LABELS = {
    "2_weeks": "2 Weeks",
    "1_month": "1 Month",
    "3_months": "3 Months",
    "6_months": "6 Months",
    "9_months": "9 Months",
    "1_year": "1 Year",
}

FORECAST_HORIZON_LABELS = {
    "1_month": "1 Month",
    "2_months": "2 Months",
    "3_months": "3 Months",
}


def classify_trend(growth_rate: float) -> str:
    """Classify trend based on growth rate.

    Args:
        growth_rate: Percentage growth rate.

    Returns:
        Trend classification string.
    """
    if pd.isna(growth_rate):
        return "No Data"
    elif growth_rate > 10:
        return "Strongly Emerging"
    elif growth_rate > 2:
        return "Emerging"
    elif growth_rate > -2:
        return "Stable"
    elif growth_rate > -10:
        return "Declining"
    else:
        return "Strongly Declining"


def calculate_growth_rate(
    df: pd.DataFrame,
    metric: str = "people_in",
    horizon_days: int = 30,
    reference_date: pd.Timestamp = None,
) -> dict | None:
    """Calculate growth rate for a given time horizon.

    Args:
        df: DataFrame with 'date' and metric columns.
        metric: Column name to calculate growth for.
        horizon_days: Number of days to look back.
        reference_date: Date to calculate from (default: max date in df).

    Returns:
        dict with growth rate info or None if insufficient data.
    """
    if df.empty:
        return None

    if reference_date is None:
        reference_date = df["date"].max()

    # Get available data range
    data_start = df["date"].min()

    # Calculate actual horizon we can use
    actual_horizon = min(horizon_days, (reference_date - data_start).days // 2)

    if actual_horizon < 7:  # Minimum 1 week of data required
        return None

    # Calculate periods with actual horizon
    current_start = reference_date - timedelta(days=actual_horizon)
    previous_start = current_start - timedelta(days=actual_horizon)

    # Current period data
    current_data = df[(df["date"] > current_start) & (df["date"] <= reference_date)]
    current_value = current_data[metric].sum()

    # Previous period data
    previous_data = df[(df["date"] > previous_start) & (df["date"] <= current_start)]
    previous_value = previous_data[metric].sum()

    # Calculate growth rate
    if previous_value == 0:
        growth_rate = np.nan
    else:
        growth_rate = ((current_value - previous_value) / previous_value) * 100

    return {
        "current_value": current_value,
        "previous_value": previous_value,
        "growth_rate": growth_rate,
        "actual_horizon_days": actual_horizon,
        "data_sufficient": actual_horizon == horizon_days,
    }


def calculate_category_trends(
    stores_enriched: pd.DataFrame,
    mall_id: int | None = None,
) -> pd.DataFrame:
    """Calculate growth rates for all categories.

    Args:
        stores_enriched: Enriched store data with date, people_in, bl1_label.
        mall_id: Optional mall ID to filter by. None = global (all malls).

    Returns:
        DataFrame with growth rates for each category and horizon.
    """
    # Filter by mall if specified
    if mall_id is not None:
        df = stores_enriched[stores_enriched["mall_id"] == mall_id]
    else:
        df = stores_enriched

    if df.empty:
        return pd.DataFrame()

    reference_date = df["date"].max()
    results = []

    # Get unique categories
    categories = df["bl1_label"].dropna().unique()

    for category in categories:
        cat_df = df[df["bl1_label"] == category]

        # Aggregate daily traffic
        daily = cat_df.groupby("date").agg({"people_in": "sum"}).reset_index()

        row = {"category": category}

        # Calculate growth for each time horizon
        for horizon_name, horizon_days in TIME_HORIZONS.items():
            growth_info = calculate_growth_rate(
                daily, "people_in", horizon_days, reference_date
            )

            if growth_info:
                row[f"{horizon_name}_growth"] = growth_info["growth_rate"]
            else:
                row[f"{horizon_name}_growth"] = np.nan

        # Add trend classification for each horizon
        for horizon_name in TIME_HORIZONS.keys():
            row[f"{horizon_name}_trend"] = classify_trend(
                row.get(f"{horizon_name}_growth")
            )

        results.append(row)

    return pd.DataFrame(results)


def forecast_category_trends(
    stores_enriched: pd.DataFrame,
    mall_id: int | None = None,
) -> pd.DataFrame:
    """Forecast growth rates for all categories using Prophet.

    Args:
        stores_enriched: Enriched store data.
        mall_id: Optional mall ID to filter by. None = global.

    Returns:
        DataFrame with forecasted growth rates.
    """
    try:
        from prophet import Prophet
    except ImportError:
        logger.warning("Prophet not available for forecasting")
        return pd.DataFrame()

    # Filter by mall if specified
    if mall_id is not None:
        df = stores_enriched[stores_enriched["mall_id"] == mall_id]
    else:
        df = stores_enriched

    if df.empty:
        return pd.DataFrame()

    results = []
    categories = df["bl1_label"].dropna().unique()

    for category in categories:
        cat_df = df[df["bl1_label"] == category]
        daily = cat_df.groupby("date").agg({"people_in": "sum"}).reset_index()

        row = {"category": category}

        # Check if enough data for forecasting
        data_days = (daily["date"].max() - daily["date"].min()).days
        if data_days < 60 or len(daily) < 30:
            for horizon_name in FORECAST_HORIZONS.keys():
                row[f"{horizon_name}_growth"] = np.nan
                row[f"{horizon_name}_trend"] = "No Data"
            results.append(row)
            continue

        # Prepare Prophet data
        prophet_df = daily[["date", "people_in"]].copy()
        prophet_df.columns = ["ds", "y"]
        prophet_df = prophet_df.dropna()

        try:
            # Fit Prophet model (suppress output)
            import logging

            logging.getLogger("prophet").setLevel(logging.WARNING)
            logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
            )
            model.fit(prophet_df)

            # Make predictions
            max_horizon = max(FORECAST_HORIZONS.values())
            future = model.make_future_dataframe(periods=max_horizon)
            forecast = model.predict(future)

            # Calculate forecasted growth rates
            current_value = prophet_df["y"].iloc[-30:].sum()
            reference_date = daily["date"].max()

            for horizon_name, horizon_days in FORECAST_HORIZONS.items():
                forecast_start = reference_date + timedelta(days=1)
                forecast_end = reference_date + timedelta(days=horizon_days)

                forecast_period = forecast[
                    (forecast["ds"] >= forecast_start)
                    & (forecast["ds"] <= forecast_end)
                ]

                if len(forecast_period) > 0:
                    forecast_value = forecast_period["yhat"].sum()
                    normalized_current = current_value * (horizon_days / 30)

                    if normalized_current > 0:
                        growth_rate = (
                            (forecast_value - normalized_current) / normalized_current
                        ) * 100
                    else:
                        growth_rate = np.nan

                    row[f"{horizon_name}_growth"] = growth_rate
                    row[f"{horizon_name}_trend"] = classify_trend(growth_rate)
                else:
                    row[f"{horizon_name}_growth"] = np.nan
                    row[f"{horizon_name}_trend"] = "No Data"

        except Exception as e:
            logger.warning(f"Forecast failed for {category}: {e}")
            for horizon_name in FORECAST_HORIZONS.keys():
                row[f"{horizon_name}_growth"] = np.nan
                row[f"{horizon_name}_trend"] = "No Data"

        results.append(row)

    return pd.DataFrame(results)


def load_stores_enriched() -> pd.DataFrame:
    """Load and enrich store data for trend calculations.

    Returns:
        DataFrame with enriched store data.
    """
    try:
        # Load data from intermediate (cleaned) files
        fact_stores = pd.read_csv(pth.INTERMEDIATE_FACT_STORES, **cst.CSV_PARAMS)
        dim_blocks = pd.read_csv(pth.INTERMEDIATE_DIM_BLOCKS, **cst.CSV_PARAMS)
        dim_malls = pd.read_csv(pth.INTERMEDIATE_DIM_MALLS, **cst.CSV_PARAMS)

        # Convert date
        fact_stores[col.DATE] = pd.to_datetime(
            fact_stores[col.DATE], format=cst.DATE_FORMAT
        )

        # Enrich with category info
        stores_enriched = fact_stores.merge(
            dim_blocks[[col.BLOCK_ID, col.CAT_HIGH, col.CAT_MID]].drop_duplicates(),
            on=col.BLOCK_ID,
            how="left",
        )

        # Rename for consistency with notebook
        stores_enriched = stores_enriched.rename(
            columns={
                col.DATE: "date",
                col.PEOPLE_IN: "people_in",
                col.MALL_ID: "mall_id",
                col.CAT_HIGH: "bl1_label",
                col.CAT_MID: "bl2_label",
            }
        )

        # Add mall name
        dim_malls = dim_malls.rename(
            columns={col.ID: "mall_id", col.MALL_NAME: "mall_name"}
        )
        stores_enriched = stores_enriched.merge(
            dim_malls[["mall_id", "mall_name"]],
            on="mall_id",
            how="left",
        )

        # Fill missing mall names
        stores_enriched["mall_name"] = stores_enriched["mall_name"].fillna(
            "Mall_" + stores_enriched["mall_id"].astype(str)
        )

        return stores_enriched

    except Exception as e:
        logger.error(f"Error loading stores enriched data: {e}")
        return pd.DataFrame()
