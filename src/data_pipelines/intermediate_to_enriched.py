"""Intermediate to enriched data processing."""

import pandas as pd

from constants import paths as pth
from src.utils.get_affinity import create_affinity_results
from src.utils.logger import logger


def process_intermediate_to_enriched():
    """Process intermediate data to create enriched datasets."""
    # Read intermediate datasets
    logger.info(f"Reading dim_blocks from {pth.INTERMEDIATE_DIM_BLOCKS}")
    dim_blocks = pd.read_csv(pth.INTERMEDIATE_DIM_BLOCKS)

    logger.info(f"Reading cross_visits from {pth.INTERMEDIATE_CROSS_VISITS}")
    cross_visits = pd.read_csv(pth.INTERMEDIATE_CROSS_VISITS)

    # Compute category affinities
    logger.info("Calculating category affinities")
    affinity_results = create_affinity_results(cross_visits, dim_blocks)

    # Save enriched datasets
    logger.info(f"Saving category affinities to {pth.ENRICHED_CATEGORY_AFFINITIES}")
    affinity_results.to_csv(pth.ENRICHED_CATEGORY_AFFINITIES, index=False)
    logger.info("Enriched data saved successfully.")


if __name__ == "__main__":
    process_intermediate_to_enriched()
