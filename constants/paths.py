"""Path configurations for the project.

This module centralizes all path definitions to ensure consistency across the project.
"""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERMEDIATE_DATA_DIR = DATA_DIR / "intermediate"

# Raw data files
DIM_MALLS = RAW_DATA_DIR / "dim_malls_v1.csv"
DIM_BLOCKS = RAW_DATA_DIR / "dim_blocks_v1.csv"
FACT_STORES = RAW_DATA_DIR / "fact_stores_v1.csv"
FACT_MALLS = RAW_DATA_DIR / "fact_malls_v1.csv"
STORE_FINANCIALS = RAW_DATA_DIR / "store_financials_v1.csv"
CROSS_VISITS = RAW_DATA_DIR / "cross_visits_v1.csv"
FACT_SRI_SCORES = RAW_DATA_DIR / "fact_sri_scores_v1.csv"

# Intermediate data files
INTERMEDIATE_DIM_MALLS = INTERMEDIATE_DATA_DIR / "dim_malls.csv"
INTERMEDIATE_DIM_BLOCKS = INTERMEDIATE_DATA_DIR / "dim_blocks.csv"
INTERMEDIATE_FACT_STORES = INTERMEDIATE_DATA_DIR / "fact_stores.csv"
INTERMEDIATE_FACT_MALLS = INTERMEDIATE_DATA_DIR / "fact_malls.csv"
INTERMEDIATE_STORE_FINANCIALS = INTERMEDIATE_DATA_DIR / "store_financials.csv"
INTERMEDIATE_CROSS_VISITS = INTERMEDIATE_DATA_DIR / "cross_visits.csv"
INTERMEDIATE_FACT_SRI_SCORES = INTERMEDIATE_DATA_DIR / "fact_sri_scores.csv"


# Configuration directory
CONFIG_DIR = PROJECT_ROOT / "config"

# Notebooks directory

# Source code directory
