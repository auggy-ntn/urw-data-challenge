"""Intermediate to Enriched Data Pipeline."""

import pandas as pd

from constants import column_names as cols
from constants import paths as pth
import constants.constants as cst
from src.utils.logger import logger


def enrich_cross_visits(
    cross_visits: pd.DataFrame, dim_blocks: pd.DataFrame
) -> pd.DataFrame:
    """Enrich the cross_visit table.

    Args:
        cross_visits (pd.DataFrame): Intermediate cross_visit table.
        dim_blocks (pd.DataFrame): Intermediate dim_blocks table.

    Returns:
        pd.DataFrame: Enriched cross_visit table with mall_id, retailer_code, and
        category information (the bl1_label, bl2_label and bl3_label).
    """
    # Select columns from dim_blocks and add suffixes for store_1
    store_1_enrich = (
        dim_blocks[
            [
                cols.STORE_CODE,
                cols.MALL_ID,
                cols.RETAILER_CODE,
                cols.CAT_HIGH,
                cols.CAT_MID,
                cols.CAT_LOW,
            ]
        ]
        .drop_duplicates(cols.STORE_CODE)
        .add_suffix(cols.SUFFIX_STORE_1)
        .copy()
    )

    # Select columns from dim_blocks and add suffixes for store_2
    store_2_enrich = (
        dim_blocks[
            [
                cols.STORE_CODE,
                cols.MALL_ID,
                cols.RETAILER_CODE,
                cols.CAT_HIGH,
                cols.CAT_MID,
                cols.CAT_LOW,
            ]
        ]
        .drop_duplicates(cols.STORE_CODE)
        .add_suffix(cols.SUFFIX_STORE_2)
        .copy()
    )

    # Merge to enrich cross_visit with store_1 information
    cross_visit_enriched = pd.merge(
        cross_visits,
        store_1_enrich,
        left_on=cols.STORE_CODE_1,
        right_on=cols.STORE_CODE + cols.SUFFIX_STORE_1,
        how="left",
        validate="m:1",
    )

    # Merge to enrich cross_visit with store_2 information
    cross_visit_enriched = pd.merge(
        cross_visit_enriched,
        store_2_enrich,
        left_on=cols.STORE_CODE_2,
        right_on=cols.STORE_CODE + cols.SUFFIX_STORE_2,
        how="left",
        validate="m:1",
    )

    # Combine mall_id columns (both stores are in the same mall)
    cross_visit_enriched[cols.MALL_ID] = cross_visit_enriched[
        cols.MALL_ID + cols.SUFFIX_STORE_1
    ].combine_first(cross_visit_enriched[cols.MALL_ID + cols.SUFFIX_STORE_2])

    # Drop redundant columns
    cross_visit_enriched = cross_visit_enriched.drop(
        columns=[cols.MALL_ID + cols.SUFFIX_STORE_1, cols.MALL_ID + cols.SUFFIX_STORE_2]
    )

    # Drop rows where mall_id is still missing after combination.
    cross_visit_enriched = cross_visit_enriched.dropna(axis=0, subset=cols.MALL_ID)

    return cross_visit_enriched


def process_intermediate_to_enriched():
    """Process intermediate to enriched data."""
    # Read intermediate data
    logger.info(f"Reading intermediate dim_blocks from {pth.INTERMEDIATE_DIM_BLOCKS}")
    dim_blocks = pd.read_csv(pth.INTERMEDIATE_DIM_BLOCKS, **cst.CSV_PARAMS)

    logger.info(
        f"Reading intermediate cross_visits from {pth.INTERMEDIATE_CROSS_VISITS}"
    )
    cross_visits = pd.read_csv(pth.INTERMEDIATE_CROSS_VISITS, **cst.CSV_PARAMS)

    # Enrich data
    logger.info("Enriching cross visit data...")
    cross_visits_enriched = enrich_cross_visits(cross_visits, dim_blocks)

    # Save enriched data
    logger.info(f"Saving cross_visits_enriched to {pth.ENRICHED_CROSS_VISITS}")
    cross_visits_enriched.to_csv(pth.ENRICHED_CROSS_VISITS, index=False)


if __name__ == "__main__":
    process_intermediate_to_enriched()
