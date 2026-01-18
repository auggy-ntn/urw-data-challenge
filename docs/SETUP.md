# Team Setup Guide

Complete setup instructions for new team members to get started with the project.

## Prerequisites

- Python 3.13+
- Git
- [uv](https://docs.astral.sh/uv/) package manager

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/auggy-ntn/urw-data-challenge.git
cd urw-data-challenge
```

### 2. Install Dependencies

```bash
# Install all project dependencies (including dev tools)
uv sync
```

This installs:
- Core dependencies (pandas, scikit-learn, streamlit, dvc, etc.)
- Development tools (ruff, pre-commit, nbstripout)

### 3. Set Up Pre-commit Hooks

```bash
uv run pre-commit install
```

This ensures code quality checks run automatically before each commit.

### 4. Configure Environment Variables

Create your `.env` file from the template:

```bash
cp .env.example .env
```

Now edit `.env` and add the DVC credentials:

#### OVH Object Storage (DVC - Data Storage)

**You'll receive these from the project owner:**

```bash
OVH_ACCESS_KEY_ID=<provided_by_owner>
OVH_SECRET_ACCESS_KEY=<provided_by_owner>
```

> **Note:** The owner will share these credentials securely. Do NOT create your own OVH account.

### 5. Configure DVC Remote

DVC needs your OVH credentials configured locally (won't be committed to git):

```bash
# Load environment variables
source .env

# Configure DVC remote with your credentials
dvc remote modify --local ovh-storage access_key_id $OVH_ACCESS_KEY_ID
dvc remote modify --local ovh-storage secret_access_key $OVH_SECRET_ACCESS_KEY
```

### 6. Pull Data from DVC

Download all project data from OVH Object Storage:

```bash
dvc pull
```

This downloads:
- Raw data in `data/raw/`
- Any processed datasets that have been shared

### 7. Verify Setup

Test that everything works:

#### Test DVC:
```bash
dvc status
# Should show: "Data and pipelines are up to date."
```

#### Run the Pipeline:
```bash
dvc repro
```

#### Launch the Dashboard:
```bash
uv run streamlit run src/streamlit/streamlit_app.py
```

## Troubleshooting

### DVC Issues

**"Unable to locate credentials"**
- Make sure your `.env` file has `OVH_ACCESS_KEY_ID` and `OVH_SECRET_ACCESS_KEY`
- Verify you've configured the DVC remote:
  ```bash
  source .env
  dvc remote modify --local ovh-storage access_key_id $OVH_ACCESS_KEY_ID
  dvc remote modify --local ovh-storage secret_access_key $OVH_SECRET_ACCESS_KEY
  ```

**"dvc pull" fails**
- Verify credentials in `.env` are correct
- Make sure you've configured the DVC remote (see above)
- Ask the project owner to confirm you're using the right credentials

### General Issues

**"Command not found: uv"**
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**"Python version mismatch"**
- This project requires Python 3.13+
- Check your version: `python --version`

**Streamlit won't start**
- Make sure you're in the project root directory
- Try: `uv run streamlit run src/streamlit/streamlit_app.py`

## Next Steps

- Read [DVC_WORKFLOW.md](DVC_WORKFLOW.md) to learn how to work with data
- Check the [README.md](../README.md) for project structure and commands
- Explore the notebooks in `notebooks/` for data analysis examples

## Getting Help

- Check existing documentation in `docs/`
- Contact the project owner for credential issues
