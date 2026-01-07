**XHEC Data Science Challenge: Multi-horizon PC price prediction for Schneider Electric**

<!-- Build & CI Status -->
![CI](https://github.com/auggy-ntn/urw-data-challenge/actions/workflows/ci.yaml/badge.svg?event=push)

<!-- Code Quality & Tools -->
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- Environment & Package Management -->
![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

---

## Quick Setup

```bash
# 1. Install dependencies with uv
uv sync

# 2. Set up environment variables (copy and edit with your credentials)
cp .env.example .env
# Edit .env and add:
#   - OVH_ACCESS_KEY_ID and OVH_SECRET_ACCESS_KEY (ask administrator for shared credentials)
#   - DATABRICKS_TOKEN (create personal access token in Databricks workspace)
#   - MLFLOW_EXPERIMENT_ID (use shared team experiment ID)

# 3. Configure DVC remote with OVH credentials
source .env
dvc remote modify --local ovh-storage access_key_id $OVH_ACCESS_KEY_ID
dvc remote modify --local ovh-storage secret_access_key $OVH_SECRET_ACCESS_KEY

# 4. Install pre-commit hooks
uv run pre-commit install

# 5. Pull data from DVC remote (OVH Object Storage)
dvc pull
```

**Important**: OVH S3 credentials are shared across the team. Contact administrator to get the `OVH_ACCESS_KEY_ID` and `OVH_SECRET_ACCESS_KEY` values.

For detailed setup instructions including how to create Databricks tokens and configure MLflow, see [docs/SETUP.md](docs/SETUP.md).\
For detailed DVC usage instructions, see [docs/DVC_WORKFLOW.md](docs/DVC_WORKFLOW.md).\
For detailed MLflow usage instructions, see [docs/MLFLOW_WORKFLOW.md](docs/MLFLOW_WORKFLOW.md).\

---
