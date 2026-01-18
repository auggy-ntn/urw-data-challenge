**XHEC Data Science Challenge: Mall Analytics for Unibail-Rodamco-Westfield**

<!-- Build & CI Status -->
![CI](https://github.com/auggy-ntn/urw-data-challenge/actions/workflows/ci.yaml/badge.svg?event=push)

<!-- Code Quality & Tools -->
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- Environment & Package Management -->
![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

---

> **For Project Owners:** If you're taking ownership of this project and need to set up infrastructure for your team (DVC remote, credentials), see **[PROJECT_OWNER_CHECKLIST.md](docs/PROJECT_OWNER_CHECKLIST.md)** for a complete setup guide.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
- [Data Pipeline](#data-pipeline)
- [Streamlit Dashboard](#streamlit-dashboard)
- [Developer Setup](#developer-setup)
- [Handover Notes](#handover-notes)

---

## Quick Start

**Want to run the pipeline and launch the dashboard? Follow these steps:**

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager (`pip install uv`)
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/auggy-ntn/urw-data-challenge.git
cd urw-data-challenge

# 2. Install dependencies
uv sync

# 3. (Optional) Set up data versioning - see "Handover Notes" if credentials are available
```

### Running the Data Pipeline

The project uses a medallion architecture (Raw → Intermediate → Enriched) with DVC orchestration:

```bash
# Run the complete pipeline (Raw → Intermediate → Enriched → Train Models)
dvc repro

# Or run stages individually:
uv run python src/data_pipelines/raw_to_intermediate.py       # Raw → Intermediate
uv run python src/data_pipelines/intermediate_to_enriched.py  # Intermediate → Enriched
uv run python -m src.utils.train_model                        # Train ML models
```

**Pipeline outputs:**
- `data/intermediate/` - Cleaned, standardized data
- `data/enriched/` - Feature-engineered datasets (store metrics, category affinities, KPIs)
- `models/` - Trained performance prediction models

### Launching the Dashboard

```**bash**
uv run streamlit run src/streamlit/streamlit_app.py
```

---

## Project Overview

This project analyzes Unibail-Rodamco-Westfield (URW) shopping mall data to provide insights into store performance and tenant mix optimization. It was developed as part of the XHEC Data Science and AI for Business course.

### Key Features

- **Mall Analytics Dashboard**: Interactive Streamlit dashboard showing KPIs, store rankings, and retail mix
- **Performance Prediction Models**: ML models predicting store capture rate, sales per sqm, and dwell time
- **Swap Predictor**: Simulates the impact of changing a store's category on overall mall performance

### Technologies

- **Data Pipeline**: DVC (Data Version Control) + Medallion architecture
- **ML Models**: Random Forest regressors for performance prediction
- **Dashboard**: Streamlit with interactive visualizations
- **Package Management**: uv
- **Code Quality**: Ruff (formatter + linter) + pre-commit hooks

---

## Project Structure

```
urw-data-challenge/
├── assets/                     # Images and static assets (URW logo)
│
├── config/                     # Configuration files
│   └── loguru.yaml            # Logging configuration
│
├── constants/                  # Centralized configuration
│   ├── column_names.py        # Column name constants
│   ├── constants.py           # Project constants
│   └── paths.py               # Path definitions
│
├── data/                       # Data directory (DVC-tracked)
│   ├── raw/                   # Raw: Immutable source data
│   ├── intermediate/          # Intermediate: Cleaned, validated data
│   └── enriched/              # Enriched: Feature-engineered, model-ready
│
├── docs/                       # Documentation
│   ├── SETUP.md               # Team setup guide
│   ├── DVC_WORKFLOW.md        # Data versioning workflow
│   └── PROJECT_OWNER_CHECKLIST.md  # Handover guide for new owners
│
├── models/                     # Trained ML models (DVC-tracked)
│   ├── *_model.joblib         # Trained model files
│   ├── *_encoders.joblib      # Label encoders for categorical features
│   └── mall_means.csv         # Mall-level normalization values
│
├── notebooks/                  # Jupyter notebooks
│   ├── eda.ipynb              # Exploratory data analysis
│   └── performance_predictor_model.ipynb  # Model development
│
├── src/
│   ├── data_pipelines/        # ETL pipelines
│   │   ├── raw_to_intermediate.py
│   │   └── intermediate_to_enriched.py
│   ├── streamlit/             # Dashboard application
│   │   ├── streamlit_app.py   # Main entry point
│   │   ├── pages.py           # Page definitions
│   │   ├── components.py      # Reusable UI components
│   │   ├── data_loading.py    # Data loading utilities
│   │   └── looks.py           # Styling and theming
│   └── utils/                 # Shared utilities
│       ├── train_model.py     # Model training pipeline
│       ├── swap_predictor.py  # Swap prediction logic
│       ├── get_affinity.py    # Category affinity calculation
│       └── logger.py          # Logging utilities
│
├── dvc.yaml                    # DVC pipeline definition
├── dvc.lock                    # DVC pipeline lock file
├── pyproject.toml              # Python dependencies and tool configuration
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .env.example                # Environment variable template
└── README.md                   # This file
```

### Data Files

**Raw data (`data/raw/`)** - Provided by URW:
- **cross_visits_v1.csv**: Cross-visitation data between stores (customer flow patterns)
- **dim_blocks_v1.csv**: Store/block dimensions (GLA, category, retailer info)
- **dim_malls_v1.csv**: Mall dimension data
- **fact_malls_v1.csv**: Daily mall-level metrics (footfall, dwell time)
- **fact_stores_v1.csv**: Daily store-level metrics (footfall, window flow, dwell time)
- **fact_sri_scores_v1.csv**: Store Retail Index (SRI) scores
- **store_financials_v1.csv**: Store financial metrics (sales, costs)

---

## Data Pipeline

### Architecture: Medallion Pattern

```
Raw (Bronze)         →    Intermediate (Silver)    →    Enriched (Gold)
data/raw/                 data/intermediate/            data/enriched/
Immutable source data     Cleaned, validated            Feature-engineered
```

### Pipeline Stages

#### Stage 1: Raw → Intermediate
Cleans and standardizes raw data:
- Renames columns to consistent naming convention
- Removes duplicates
- Handles invalid values

#### Stage 2: Intermediate → Enriched
Creates feature-engineered datasets:
- **store_metrics.csv**: Aggregated store performance metrics
- **category_affinities.csv**: Jaccard similarity between store categories
- **category_sri_avg.csv**: Average SRI scores by category
- **mall_kpis.csv**: Mall-level KPIs for dashboard
- **store_kpis.csv**: Store-level KPIs for dashboard

#### Stage 3: Train Models
Trains Random Forest models to predict:
- **Capture Rate**: Ratio of window flow to store entries
- **Sales per Sqm**: Normalized sales performance
- **Dwell Time**: Average time spent in store

---

## Streamlit Dashboard

### Main Dashboard
- Portfolio-level KPIs (footfall, dwell time, revenue)
- Mall selection cards

### Mall Detail View
- Mall-specific KPIs with trend indicators
- Retail mix pie chart (category distribution)
- Store rankings (sortable by footfall, revenue, dwell time, OCR)
- **Swap Predictor**: Simulate tenant changes

### Swap Predictor
The swap predictor estimates the impact of changing a store's category:
1. Select a store to "swap"
2. Choose a new category
3. View predicted impact on:
   - Sales per sqm
   - Dwell time
   - SRI score
   - Composite mall score

---

## Developer Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Installation

```bash
# 1. Clone and navigate to project
git clone https://github.com/auggy-ntn/urw-data-challenge.git
cd urw-data-challenge

# 2. Install all dependencies (runtime + dev)
uv sync

# 3. Install pre-commit hooks
uv run pre-commit install
```

### Code Quality Tools

All tools are configured in `pyproject.toml` and run automatically via pre-commit:

```bash
# Format code (88 char line length)
uv run ruff format .

# Lint and auto-fix issues
uv run ruff check --fix .

# Run all pre-commit hooks manually
uv run pre-commit run --all-files
```

**Pre-commit hooks:**
- `ruff format` - Code formatting
- `ruff check` - Linting (includes import sorting, docstring style)
- `nbstripout` - Strip Jupyter notebook outputs
- `trailing-whitespace`, `end-of-file-fixer` - File hygiene

### Adding Dependencies

```bash
# Add runtime dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Sync environment after manual pyproject.toml edits
uv sync
```

---

## Handover Notes

**This project is being transferred to new ownership. Please note:**

### Remote Infrastructure (Not Included)

The original project used remote services that **may not be accessible** to new owners:

#### DVC Remote Storage (OVH Object Storage)
- **Original setup**: Data versioning backed by OVH S3-compatible storage
- **Impact**: You may not be able to `dvc pull` from the original remote
- **Solution**: Set up your own DVC remote storage (see [PROJECT_OWNER_CHECKLIST.md](docs/PROJECT_OWNER_CHECKLIST.md))

### What IS Included (Fully Functional)

- **Complete codebase**: All pipelines, models, and dashboard code
- **DVC pipeline definitions**: `dvc.yaml` and `dvc.lock`
- **Documentation**: Setup guides and workflow documentation
- **Development tools**: Pre-commit hooks, CI/CD pipeline

### Getting Started Without Remote Services

You can **fully use this project** without remote services if you have the raw data:

```bash
# 1. Clone and install
git clone https://github.com/auggy-ntn/urw-data-challenge.git
cd urw-data-challenge
uv sync

# 2. Place raw data files in data/raw/ (see Data Files section above)

# 3. Run the pipeline
uv run python src/data_pipelines/raw_to_intermediate.py
uv run python src/data_pipelines/intermediate_to_enriched.py
uv run python -m src.utils.train_model

# 4. Launch the dashboard
uv run streamlit run src/streamlit/streamlit_app.py
```

---

## Additional Documentation

- **[PROJECT_OWNER_CHECKLIST.md](docs/PROJECT_OWNER_CHECKLIST.md)** - Setup guide for new project owners
- **[SETUP.md](docs/SETUP.md)** - Complete developer setup guide
- **[DVC_WORKFLOW.md](docs/DVC_WORKFLOW.md)** - Data versioning workflow

---

## Authors

**XHEC Data Science Challenge Team**
- William BELAIDI
- Grégoire BIDAULT
- Aymeric DE LONGEVIALLE
- Paul FILISETTI
- Augustin NATON
- Louis PERETIE

---
