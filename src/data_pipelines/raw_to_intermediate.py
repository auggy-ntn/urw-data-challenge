"""Raw to intermediate data processing."""

import pandas as pd

from constants import column_names as cols
from constants import constants as cst
from constants import paths as pth
from src.utils.logger import logger


def clean_dim_blocks(dim_blocks: pd.DataFrame) -> pd.DataFrame:
    """Clean the dim_blocks table.

    Args:
        dim_blocks (pd.DataFrame): Raw dim_blocks table.

    Returns:
        pd.DataFrame: Cleaned dim_blocks table.
    """
    # Rename columns
    dim_blocks.columns = cols.DIM_BLOCKS_COLUMNS

    # Drop duplicates
    dim_blocks = dim_blocks.drop_duplicates()

    return dim_blocks


def clean_dim_malls(dim_malls: pd.DataFrame) -> pd.DataFrame:
    """Clean the dim_malls table.

    Args:
        dim_malls (pd.DataFrame): Raw dim_malls table.

    Returns:
        pd.DataFrame: Cleaned dim_malls table.
    """
    # Rename columns
    dim_malls.columns = cols.DIM_MALLS_COLUMNS

    # Drop duplicates
    dim_malls = dim_malls.drop_duplicates()

    return dim_malls


def clean_fact_stores(fact_stores: pd.DataFrame) -> pd.DataFrame:
    """Clean the fact_stores table.

    Args:
        fact_stores (pd.DataFrame): Raw fact_stores table.

    Returns:
        pd.DataFrame: Cleaned fact_stores table.
    """
    # Rename columns
    fact_stores.columns = cols.FACT_STORES_COLUMNS

    # Drop duplicates
    fact_stores = fact_stores.drop_duplicates()

    return fact_stores


def clean_fact_malls(fact_malls: pd.DataFrame) -> pd.DataFrame:
    """Clean the fact_malls table.

    Args:
        fact_malls (pd.DataFrame): Raw fact_malls table.

    Returns:
        pd.DataFrame: Cleaned fact_malls table.
    """
    # Rename columns
    fact_malls.columns = cols.FACT_MALLS_COLUMNS

    # Drop duplicates
    fact_malls = fact_malls.drop_duplicates()

    return fact_malls


def clean_fact_sri_scores(fact_sri_scores: pd.DataFrame) -> pd.DataFrame:
    """Clean the fact_sri_scores table.

    Args:
        fact_sri_scores (pd.DataFrame): Raw fact_sri_scores table.

    Returns:
        pd.DataFrame: Cleaned fact_sri_scores table.
    """
    # Rename columns
    fact_sri_scores.columns = cols.FACT_SRI_SCORES_COLUMNS

    # Drop duplicates
    fact_sri_scores = fact_sri_scores.drop_duplicates()

    return fact_sri_scores


def clean_store_financials(store_financials: pd.DataFrame) -> pd.DataFrame:
    """Clean the store_financials table.

    Args:
        store_financials (pd.DataFrame): Raw store_financials table.

    Returns:
        pd.DataFrame: Cleaned store_financials table.
    """
    # Rename columns
    store_financials.columns = cols.STORE_FINANCIALS_COLUMNS

    # Drop duplicates
    store_financials = store_financials.drop_duplicates()

    return store_financials


def clean_cross_visits(cross_visits: pd.DataFrame) -> pd.DataFrame:
    """Clean the cross_visits table.

    Args:
        cross_visits (pd.DataFrame): Raw cross_visits table.

    Returns:
        pd.DataFrame: Cleaned cross_visits table.
    """
    # Rename columns
    cross_visits.columns = cols.CROSS_VISITS_COLUMNS

    # Drop duplicates
    cross_visits = cross_visits.drop_duplicates()

    return cross_visits


def process_raw_to_intermediate():
    """Process raw data to intermediate data."""
    # Read raw data
    logger.info(f"Reading raw dim_blocks from {pth.DIM_BLOCKS}")
    dim_blocks = pd.read_csv(pth.DIM_BLOCKS, **cst.CSV_PARAMS)

    logger.info(f"Reading raw dim_malls from {pth.DIM_MALLS}")
    dim_malls = pd.read_csv(pth.DIM_MALLS, **cst.CSV_PARAMS)

    logger.info(f"Reading raw fact_stores from {pth.FACT_STORES}")
    fact_stores = pd.read_csv(pth.FACT_STORES, **cst.CSV_PARAMS)

    logger.info(f"Reading raw fact_malls from {pth.FACT_MALLS}")
    fact_malls = pd.read_csv(pth.FACT_MALLS, **cst.CSV_PARAMS)

    logger.info(f"Reading raw fact_sri_scores from {pth.FACT_SRI_SCORES}")
    fact_sri_scores = pd.read_csv(pth.FACT_SRI_SCORES, **cst.CSV_PARAMS)

    logger.info(f"Reading raw store_financials from {pth.STORE_FINANCIALS}")
    store_financials = pd.read_csv(pth.STORE_FINANCIALS, **cst.CSV_PARAMS)

    logger.info(f"Reading raw cross_visits from {pth.CROSS_VISITS}")
    cross_visits = pd.read_csv(pth.CROSS_VISITS, **cst.CSV_PARAMS)

    # Clean data
    logger.info("Cleaning raw data to intermediate format")
    dim_blocks = clean_dim_blocks(dim_blocks)
    dim_malls = clean_dim_malls(dim_malls)
    fact_stores = clean_fact_stores(fact_stores)
    fact_malls = clean_fact_malls(fact_malls)
    fact_sri_scores = clean_fact_sri_scores(fact_sri_scores)
    store_financials = clean_store_financials(store_financials)
    cross_visits = clean_cross_visits(cross_visits)

    # Save intermediate data
    logger.info(f"Saving intermediate dim_blocks to {pth.INTERMEDIATE_DIM_BLOCKS}")
    dim_blocks.to_csv(pth.INTERMEDIATE_DIM_BLOCKS, index=False)

    logger.info(f"Saving intermediate dim_malls to {pth.INTERMEDIATE_DIM_MALLS}")
    dim_malls.to_csv(pth.INTERMEDIATE_DIM_MALLS, index=False)

    logger.info(f"Saving intermediate fact_stores to {pth.INTERMEDIATE_FACT_STORES}")
    fact_stores.to_csv(pth.INTERMEDIATE_FACT_STORES, index=False)

    logger.info(f"Saving intermediate fact_malls to {pth.INTERMEDIATE_FACT_MALLS}")
    fact_malls.to_csv(pth.INTERMEDIATE_FACT_MALLS, index=False)

    logger.info(
        f"Saving intermediate fact_sri_scores to {pth.INTERMEDIATE_FACT_SRI_SCORES}"
    )
    fact_sri_scores.to_csv(pth.INTERMEDIATE_FACT_SRI_SCORES, index=False)

    logger.info(
        f"Saving intermediate store_financials to {pth.INTERMEDIATE_STORE_FINANCIALS}"
    )
    store_financials.to_csv(pth.INTERMEDIATE_STORE_FINANCIALS, index=False)

    logger.info(f"Saving intermediate cross_visits to {pth.INTERMEDIATE_CROSS_VISITS}")
    cross_visits.to_csv(pth.INTERMEDIATE_CROSS_VISITS, index=False)
    logger.info("Intermediate data saved successfully.")


if __name__ == "__main__":
    process_raw_to_intermediate()
