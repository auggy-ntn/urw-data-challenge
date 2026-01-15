"""Intermediate to enriched data processing."""

import pandas as pd

from constants import column_names as col
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

    # Compute store metrics
    logger.info("Calculating store metrics")
    store_metrics = build_store_metrics(fact_stores)

    # Compute category affinities
    logger.info("Calculating category affinities")
    affinity_results = create_affinity_results(cross_visits, dim_blocks)

    # Compute average SRI scores per category
    logger.info("Calculating category SRI averages")
    category_sri_avg = compute_category_sri_averages(fact_sri_scores, dim_blocks)

    # Save enriched datasets
    pth.ENRICHED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving store metrics to {pth.ENRICHED_STORE_METRICS}")
    store_metrics.to_csv(pth.ENRICHED_STORE_METRICS, index=True)

    logger.info(f"Saving category affinities to {pth.ENRICHED_CATEGORY_AFFINITIES}")
    affinity_results.to_csv(pth.ENRICHED_CATEGORY_AFFINITIES, index=False)

    logger.info(f"Saving category SRI averages to {pth.ENRICHED_CATEGORY_SRI_AVG}")
    category_sri_avg.to_csv(pth.ENRICHED_CATEGORY_SRI_AVG, index=True)

    logger.info("Enriched data saved successfully.")


if __name__ == "__main__":
    process_intermediate_to_enriched()
