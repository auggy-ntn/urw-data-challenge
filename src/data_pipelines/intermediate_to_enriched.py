"""Intermediate to enriched data processing."""

import pandas as pd

from constants import column_names as col
from constants import constants as cst
from constants import paths as pth
from src.utils.get_affinity import create_affinity_results
from src.utils.logger import logger


def build_store_metrics(fact_stores: pd.DataFrame) -> pd.DataFrame:
    """Build store metrics from fact_stores data.

    Args:
        fact_stores (pd.DataFrame): Fact stores data.

    Returns:
            pd.DataFrame: DataFrame with aggregated store metrics.
    """
    # For stores that span multiple blocks, we take the sum of the people window flow
    # over all blocks
    store_daily = (
        fact_stores.groupby([col.STORE_CODE, col.DATE])
        .agg(
            **{
                col.PEOPLE_WINDOW_FLOW: (col.PEOPLE_WINDOW_FLOW, "sum"),
                col.PEOPLE_IN: (col.PEOPLE_IN, "sum"),
                col.STORE_AVG_DWELL_TIME: (col.STORE_AVG_DWELL_TIME, "mean"),
            }
        )
        .reset_index()
    )

    store_total = store_daily.groupby(col.STORE_CODE).agg(
        **{
            col.MODEL_STORE_AVG_WINDOW_FLOW: (col.PEOPLE_WINDOW_FLOW, "mean"),
            col.MODEL_STORE_MEDIAN_WINDOW_FLOW: (col.PEOPLE_WINDOW_FLOW, "median"),
            col.MODEL_STORE_TOTAL_PEOPLE_IN: (col.PEOPLE_IN, "sum"),
            col.MODEL_STORE_TOTAL_WINDOW_FLOW: (col.PEOPLE_WINDOW_FLOW, "sum"),
            col.MODEL_STORE_DAYS_RECORDED: (col.DATE, "nunique"),
            col.MODEL_STORE_AVG_DWELL_TIME: (col.STORE_AVG_DWELL_TIME, "mean"),
        }
    )

    return store_total


def compute_category_sri_averages(
    fact_sri_scores: pd.DataFrame,
    dim_blocks: pd.DataFrame,
) -> dict:
    """Compute average SRI score for each category.

    Args:
        fact_sri_scores: DataFrame with store_code and sri_score.
        dim_blocks: Dimension table for blocks (to get category).

    Returns:
        Dictionary mapping category to average SRI score.
    """
    sri_with_cat = pd.merge(
        fact_sri_scores,
        dim_blocks[[col.STORE_CODE, col.CAT_HIGH]].drop_duplicates(),
        on=col.STORE_CODE,
        how="left",
    )
    return sri_with_cat.groupby(col.CAT_HIGH)[col.SRI_SCORE].mean()


def build_mall_kpis(
    dim_malls: pd.DataFrame,
    dim_blocks: pd.DataFrame,
    fact_malls: pd.DataFrame,
    fact_stores: pd.DataFrame,
    store_financials: pd.DataFrame,
    window_size: int = cst.WINDOW_SIZE,
) -> pd.DataFrame:
    """Build dataframe with mall KPIs for dashboard.

    Args:
        dim_malls (pd.DataFrame): Mall general data.
        dim_blocks (pd.DataFrame): Block & store general data.
        fact_malls (pd.DataFrame): Mall fact data.
        fact_stores (pd.DataFrame): Store fact data.
        store_financials (pd.DataFrame): Store financial data.
        window_size (int, Optional): Window size in months for KPI calculation.

    Returns:
        pd.DataFrame: DataFrame with mall KPIs.
    """
    # Mapping of store to mall
    store_to_mall = (
        fact_stores[[col.STORE_CODE, col.MALL_ID]]
        .drop_duplicates()
        .set_index(col.STORE_CODE)
    )

    # Total sales per mall over the last 12 months
    mall_sales = (
        store_to_mall.merge(
            store_financials[[col.STORE_CODE, col.SALES_R12M]].set_index(
                col.STORE_CODE
            ),
            left_index=True,
            right_index=True,
        )
        .groupby(col.MALL_ID)[col.SALES_R12M]
        .sum()
    ).rename(col.TOTAL_MALL_SALES)
    mall_sales = mall_sales / 1_000_000  # Convert to millions

    # Prepare fact_malls with date filtering
    fact_malls[col.DATE] = pd.to_datetime(fact_malls[col.DATE], format=cst.DATE_FORMAT)

    max_date = fact_malls[col.DATE].max()

    after_cutoff_mask = fact_malls[col.DATE] > max_date - pd.DateOffset(
        months=window_size
    )
    before_cutoff_mask = fact_malls[col.DATE] <= max_date - pd.DateOffset(
        months=window_size
    )

    fact_malls_after_cutoff = fact_malls[after_cutoff_mask]
    fact_malls_before_cutoff = fact_malls[before_cutoff_mask]

    mall_kpis = pd.DataFrame()

    mall_kpis.index = dim_malls[col.ID].unique()
    mall_kpis = pd.merge(
        mall_kpis,
        fact_malls_after_cutoff.groupby(col.MALL_ID).agg(
            {col.PEOPLE_IN: "mean", col.AVG_DWELL_TIME: "mean"}
        ),
        left_index=True,
        right_index=True,
        how="left",
        validate="1:1",
    ).rename(
        columns={
            col.PEOPLE_IN: col.DAILY_PEOPLE_IN_LAST_XM,
            col.AVG_DWELL_TIME: col.AVG_DWELL_TIME_LAST_XM,
        }
    )

    mall_kpis = pd.merge(
        mall_kpis,
        fact_malls_before_cutoff.groupby(col.MALL_ID).agg(
            {col.PEOPLE_IN: "mean", col.AVG_DWELL_TIME: "mean"}
        ),
        left_index=True,
        right_index=True,
        how="left",
        validate="1:1",
    ).rename(
        columns={
            col.PEOPLE_IN: col.DAILY_PEOPLE_IN_BEFORE_XM,
            col.AVG_DWELL_TIME: col.AVG_DWELL_TIME_BEFORE_XM,
        }
    )

    mall_kpis[col.PCT_CHANGE_PEOPLE_IN] = (
        (
            mall_kpis[col.DAILY_PEOPLE_IN_LAST_XM]
            - mall_kpis[col.DAILY_PEOPLE_IN_BEFORE_XM]
        )
        / mall_kpis[col.DAILY_PEOPLE_IN_BEFORE_XM]
        * 100
    )

    mall_kpis[col.PCT_CHANGE_AVG_DWELL_TIME] = (
        (
            mall_kpis[col.AVG_DWELL_TIME_LAST_XM]
            - mall_kpis[col.AVG_DWELL_TIME_BEFORE_XM]
        )
        / mall_kpis[col.AVG_DWELL_TIME_BEFORE_XM]
        * 100
    )

    mall_kpis = mall_kpis.merge(
        mall_sales, left_index=True, right_index=True, how="left", validate="1:1"
    )

    # Create percentage distribution of bl1_label per mall
    store_label_dist = (
        dim_blocks.drop_duplicates(subset=[col.STORE_CODE])
        .groupby([col.MALL_ID, col.CAT_HIGH])
        .size()
        .unstack(fill_value=0)
    )

    # Convert to percentages
    store_label_pct = store_label_dist.div(store_label_dist.sum(axis=1), axis=0) * 100

    # Rename columns to be more descriptive
    store_label_pct.columns = [f"pct_{label}" for label in store_label_pct.columns]

    mall_kpis = mall_kpis.merge(
        store_label_pct,
        left_index=True,
        right_index=True,
        how="left",
        validate="1:1",
    )

    return mall_kpis


def build_store_kpis(
    fact_stores: pd.DataFrame,
    store_financials: pd.DataFrame,
    dim_blocks: pd.DataFrame,
    window_size: int = 1,
) -> pd.DataFrame:
    """Build store KPIs.

    Args:
        fact_stores (pd.DataFrame): Store fact data.
        store_financials (pd.DataFrame): Store financial data.
        dim_blocks (pd.DataFrame): Dimension table for blocks.
        window_size (int, optional): Window size in months. Defaults to 1.

    Returns:
        pd.DataFrame: Store KPIs.
    """
    store_to_mall = (
        fact_stores[[col.STORE_CODE, col.MALL_ID]]
        .drop_duplicates()
        .set_index(col.STORE_CODE)
    )

    store_to_retailer = dim_blocks.drop_duplicates(subset=col.STORE_CODE)[
        [col.STORE_CODE, col.RETAILER_CODE, col.STORE_NAME, col.CAT_HIGH]
    ].set_index(col.STORE_CODE)

    store_to_mall = store_to_mall.merge(
        store_to_retailer, left_index=True, right_index=True, how="left", validate="1:1"
    )

    store_kpis = store_to_mall.merge(
        store_financials.set_index(col.STORE_CODE),
        left_index=True,
        right_index=True,
        how="left",
        validate="1:1",
    )

    store_kpis[col.OCR] = store_kpis[col.SALES_R12M] / store_kpis[col.TOTAL_COSTS_R12M]

    # Prepare fact_stores with date filtering
    fact_stores[col.DATE] = pd.to_datetime(
        fact_stores[col.DATE], format=cst.DATE_FORMAT
    )

    max_date = fact_stores[col.DATE].max()

    after_cutoff_mask = fact_stores[col.DATE] > max_date - pd.DateOffset(
        months=window_size
    )
    before_cutoff_mask = fact_stores[col.DATE] <= max_date - pd.DateOffset(
        months=window_size
    )

    fact_stores_after_cutoff = fact_stores[after_cutoff_mask]
    fact_stores_before_cutoff = fact_stores[before_cutoff_mask]

    fact_stores_after_cutoff = (
        fact_stores_after_cutoff.groupby([col.DATE, col.STORE_CODE])
        .agg({col.PEOPLE_IN: "sum", col.STORE_AVG_DWELL_TIME: "mean"})
        .reset_index()
    )
    fact_stores_after_cutoff = fact_stores_after_cutoff.groupby(col.STORE_CODE).agg(
        {col.PEOPLE_IN: "mean", col.STORE_AVG_DWELL_TIME: "mean"}
    )

    fact_stores_before_cutoff = (
        fact_stores_before_cutoff.groupby([col.DATE, col.STORE_CODE])
        .agg({col.PEOPLE_IN: "sum", col.STORE_AVG_DWELL_TIME: "mean"})
        .reset_index()
    )
    fact_stores_before_cutoff = fact_stores_before_cutoff.groupby(col.STORE_CODE).agg(
        {col.PEOPLE_IN: "mean", col.STORE_AVG_DWELL_TIME: "mean"}
    )

    store_kpis = pd.merge(
        store_kpis,
        fact_stores_after_cutoff,
        left_index=True,
        right_index=True,
        how="left",
        validate="1:1",
    ).rename(
        columns={
            col.PEOPLE_IN: col.DAILY_PEOPLE_IN_LAST_XM,
            col.STORE_AVG_DWELL_TIME: col.AVG_DWELL_TIME_LAST_XM,
        }
    )

    store_kpis = pd.merge(
        store_kpis,
        fact_stores_before_cutoff,
        left_index=True,
        right_index=True,
        how="left",
        validate="1:1",
    ).rename(
        columns={
            col.PEOPLE_IN: col.DAILY_PEOPLE_IN_BEFORE_XM,
            col.STORE_AVG_DWELL_TIME: col.AVG_DWELL_TIME_BEFORE_XM,
        }
    )

    store_kpis["pct_change_people_in"] = (
        (
            store_kpis[col.DAILY_PEOPLE_IN_LAST_XM]
            - store_kpis[col.DAILY_PEOPLE_IN_BEFORE_XM]
        )
        / store_kpis[col.DAILY_PEOPLE_IN_BEFORE_XM]
        * 100
    )

    store_kpis[col.PCT_CHANGE_AVG_DWELL_TIME] = (
        (
            store_kpis[col.AVG_DWELL_TIME_LAST_XM]
            - store_kpis[col.AVG_DWELL_TIME_BEFORE_XM]
        )
        / store_kpis[col.AVG_DWELL_TIME_BEFORE_XM]
        * 100
    )

    return store_kpis


def process_intermediate_to_enriched():
    """Process intermediate data to create enriched datasets."""
    # Read intermediate datasets
    logger.info(f"Reading dim_blocks from {pth.INTERMEDIATE_DIM_BLOCKS}")
    dim_blocks = pd.read_csv(pth.INTERMEDIATE_DIM_BLOCKS)

    logger.info(f"Reading cross_visits from {pth.INTERMEDIATE_CROSS_VISITS}")
    cross_visits = pd.read_csv(pth.INTERMEDIATE_CROSS_VISITS)

    logger.info(f"Reading fact_stores from {pth.INTERMEDIATE_FACT_STORES}")
    fact_stores = pd.read_csv(pth.INTERMEDIATE_FACT_STORES)

    logger.info(f"Reading fact_sri_scores from {pth.INTERMEDIATE_FACT_SRI_SCORES}")
    fact_sri_scores = pd.read_csv(pth.INTERMEDIATE_FACT_SRI_SCORES)

    logger.info(f"Reading fact_malls from {pth.INTERMEDIATE_FACT_MALLS}")
    fact_malls = pd.read_csv(pth.INTERMEDIATE_FACT_MALLS)

    logger.info(f"Reading dim_malls from {pth.INTERMEDIATE_DIM_MALLS}")
    dim_malls = pd.read_csv(pth.INTERMEDIATE_DIM_MALLS)

    logger.info(f"Reading store_financials from {pth.INTERMEDIATE_STORE_FINANCIALS}")
    store_financials = pd.read_csv(pth.INTERMEDIATE_STORE_FINANCIALS)

    # Compute store metrics
    logger.info("Calculating store metrics")
    store_metrics = build_store_metrics(fact_stores)

    # Compute category affinities
    logger.info("Calculating category affinities")
    affinity_results = create_affinity_results(cross_visits, dim_blocks)

    # Compute average SRI scores per category
    logger.info("Calculating category SRI averages")
    category_sri_avg = compute_category_sri_averages(fact_sri_scores, dim_blocks)

    # Compute mall KPIs
    logger.info("Calculating mall KPIs")
    mall_kpis = build_mall_kpis(
        dim_malls, dim_blocks, fact_malls, fact_stores, store_financials
    )

    # Compute store KPIs
    logger.info("Calculating store KPIs")
    store_kpis = build_store_kpis(fact_stores, store_financials, dim_blocks)

    # Save enriched datasets
    pth.ENRICHED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving store metrics to {pth.ENRICHED_STORE_METRICS}")
    store_metrics.to_csv(pth.ENRICHED_STORE_METRICS, index=True)

    logger.info(f"Saving category affinities to {pth.ENRICHED_CATEGORY_AFFINITIES}")
    affinity_results.to_csv(pth.ENRICHED_CATEGORY_AFFINITIES, index=False)

    logger.info(f"Saving category SRI averages to {pth.ENRICHED_CATEGORY_SRI_AVG}")
    category_sri_avg.to_csv(pth.ENRICHED_CATEGORY_SRI_AVG, index=True)

    logger.info(f"Saving mall KPIs to {pth.ENRICHED_MALL_KPIS}")
    mall_kpis.to_csv(pth.ENRICHED_MALL_KPIS, index=True)

    logger.info(f"Saving store KPIs to {pth.ENRICHED_STORE_KPIS}")
    store_kpis.to_csv(pth.ENRICHED_STORE_KPIS, index=True)

    logger.info("Enriched data saved successfully.")


if __name__ == "__main__":
    process_intermediate_to_enriched()
