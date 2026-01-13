# URW x HEC Data Challenge - Project Roadmap

## Project Goal

**Design a data-driven framework to assess, simulate, and recommend optimal retail mixes** that maximize the overall value of URW shopping centers in terms of revenue, visitor engagement, efficiency, and future-readiness.

The primary deliverable is a **robust analytical approach** with clear justification, not just raw results.

### Key Business Questions

1. What is the "ideal" tenant composition for a given mall profile?
2. How does adding, removing, or relocating a tenant impact others and the mall as a whole?
3. How can URW proactively adapt the retail mix to emerging trends?

---

## Architecture Overview: The Three-Layer Swap Engine

Our approach separates the problem into three distinct layers, each with a clear responsibility:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 3: SWAP SIMULATOR                      │
│  "What happens if we replace Store X with Category Y?"          │
│  - Removes old store from graph                                 │
│  - Estimates new store's connections using Layer 1              │
│  - Predicts performance using Layer 2                           │
│  - Computes second-order effects on neighbors                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 2: PERFORMANCE MODEL                      │
│  "Given a store's context, how well will it perform?"           │
│  - Predicts capture_rate, sales_per_sqm, dwell_time             │
│  - Uses store features + neighborhood synergy features          │
│  - Trained on observed store performance                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               LAYER 1: SYNERGY QUANTIFICATION                   │
│  "Which categories naturally attract each other's customers?"   │
│  - Computes lift-based affinity (not raw cross-visits)          │
│  - Aggregates to category level for transferability             │
│  - Provides the "wiring diagram" for new stores                 │
└─────────────────────────────────────────────────────────────────┘
```

**Why this architecture?**
- **Separation of concerns**: Synergy patterns are learned separately from performance prediction
- **Transferability**: Category affinity learned from all 22 malls can be applied to any mall
- **Counterfactual reasoning**: We can predict what *would* happen with a new store

---

## KPIs and Metrics Framework

### Mall-Level Composite Score

We define a weighted composite score to evaluate mall "health":

```python
def compute_mall_score(mall_data, weights):
    """
    Compute composite mall score balancing multiple objectives.

    Args:
        mall_data: Aggregated mall metrics
        weights: Dict of objective weights (should sum to 1)

    Returns:
        Composite score (higher is better)
    """
    # Normalize each metric to [0, 1] using min-max across all malls
    scores = {
        'revenue_efficiency': normalize(mall_data['total_sales'] / mall_data['total_gla']),
        'traffic_efficiency': normalize(mall_data['total_footfall'] / mall_data['total_gla']),
        'engagement': normalize(mall_data['avg_dwell_time']),
        'diversity': compute_diversity_index(mall_data['category_distribution']),
        'sustainability': normalize(mall_data['avg_sri_score']),
    }

    return sum(weights[k] * scores[k] for k in weights)
```

**Why a composite score?**
- URW needs to balance multiple objectives (revenue vs sustainability vs diversity)
- Allows stakeholders to adjust weights based on strategic priorities
- Provides a single metric to compare "before vs after" in swap simulations

### Store-Level Performance Metrics

| Metric | Formula | Data Source | Why It Matters |
|--------|---------|-------------|----------------|
| **Capture Rate** | `people_in / people_window_flow` | `fact_stores_v1` | Measures conversion: of people who pass, how many enter? |
| **Sales per sqm** | `sales_r12m / gla` | `store_financials_v1`, `dim_blocks_v1` | Revenue efficiency normalized by size |
| **OCR** | `total_costs_r12m / sales_r12m` | `store_financials_v1` | Tenant financial health (lower is better) |
| **Dwell Time** | `store_average_dwell_time` | `fact_stores_v1` | Customer engagement |
| **Synergy Contribution** | See Layer 1 | `cross_visits_v1` | How much does this store boost neighbors? |
| **SRI Score** | `sri_score` | `fact_sri_scores_v1` | Sustainability rating |

### Retail Mix Quality Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| **Category Diversity (Shannon)** | `-Σ(p_i × log(p_i))` | Penalize over-concentration in one category |
| **Anchor Coverage** | `Σ(anchor_gla) / total_gla` | Ensure sufficient traffic drivers |
| **Avg Neighbor Synergy** | `mean(lift_scores)` | Are categories well-matched? |
| **Sustainability Mix** | `Σ(sri × gla) / total_gla` | GLA-weighted sustainability |

---

## Phase 1: Data Foundation & Exploration

### 1.1 Data Ingestion & Quality Assessment

**Objective**: Load all datasets, validate integrity, document issues.

**Data Required**:
- `dim_blocks_v1.csv`: Store metadata (store_code, mall_id, retailer_code, gla, categories)
- `fact_stores_v1.csv`: Daily store metrics (~90MB, largest file)
- `fact_malls_v1.csv`: Daily mall metrics
- `store_financials_v1.csv`: 12-month sales and costs
- `cross_visits_v1.csv`: Pairwise cross-visit counts
- `fact_sri_scores_v1.csv`: Sustainability scores

```python
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")

# Load all tables
dim_blocks = pd.read_csv(DATA_DIR / "dim_blocks_v1.csv")
fact_stores = pd.read_csv(DATA_DIR / "fact_stores_v1.csv", parse_dates=["date"])
fact_malls = pd.read_csv(DATA_DIR / "fact_malls_v1.csv", parse_dates=["date"])
store_financials = pd.read_csv(DATA_DIR / "store_financials_v1.csv")
cross_visits = pd.read_csv(DATA_DIR / "cross_visits_v1.csv")
fact_sri = pd.read_csv(DATA_DIR / "fact_sri_scores_v1.csv")

# Validate joins
assert dim_blocks["store_code"].is_unique, "Duplicate store_codes in dim_blocks!"
assert set(fact_stores["store_code"]).issubset(set(dim_blocks["store_code"])), \
    "Orphan store_codes in fact_stores!"
```

**Quality Checks**:

```python
def profile_dataframe(df, name):
    """Generate data quality report for a DataFrame."""
    report = {
        "name": name,
        "rows": len(df),
        "columns": len(df.columns),
        "missing_pct": (df.isnull().sum() / len(df) * 100).to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }
    return report

# Check financial data coverage
financial_coverage = store_financials["codstr"].nunique() / dim_blocks["store_code"].nunique()
print(f"Financial data covers {financial_coverage:.1%} of stores")

# Check cross-visit coverage by mall
cross_visits_enriched = cross_visits.merge(
    dim_blocks[["store_code", "mall_id"]],
    left_on="store_code_1",
    right_on="store_code"
)
print(cross_visits_enriched.groupby("mall_id").size())
```

### 1.2 Exploratory Data Analysis

**Objective**: Understand data distributions, identify patterns, inform modeling choices.

**Key Questions**:
1. How do the 22 malls differ in size, footfall, and category mix?
2. What's the distribution of store performance within categories?
3. Are there temporal patterns (day-of-week, seasonality)?
4. What's the structure of the cross-visit network?

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Mall comparison
mall_summary = (
    dim_blocks.groupby("mall_id")
    .agg(
        n_stores=("store_code", "nunique"),
        total_gla=("gla", "sum"),
        n_categories=("bl1_label", "nunique"),
    )
    .merge(
        fact_malls.groupby("mall_id")["people_in"].mean(),
        on="mall_id"
    )
)
mall_summary["footfall_per_sqm"] = mall_summary["people_in"] / mall_summary["total_gla"]

# Category performance distribution
store_perf = (
    fact_stores.groupby("store_code")
    .agg(
        avg_people_in=("people_in", "mean"),
        avg_window_flow=("people_window_flow", "mean"),
    )
    .assign(capture_rate=lambda x: x["avg_people_in"] / x["avg_window_flow"])
    .merge(dim_blocks[["store_code", "bl1_label", "gla"]], on="store_code")
)

# Plot capture rate by category
fig, ax = plt.subplots(figsize=(12, 6))
store_perf.boxplot(column="capture_rate", by="bl1_label", ax=ax, rot=45)
ax.set_title("Capture Rate Distribution by Category")
```

### Deliverables
- [ ] Data quality report (missing values, coverage, anomalies)
- [ ] EDA notebook with visualizations
- [ ] Key insights document

---

## Phase 2: Synergy Quantification (Layer 1)

### 2.1 The Problem with Raw Cross-Visits

**Why we can't use raw cross-visits directly**:

Raw cross-visit counts are misleading because:
- High-traffic stores have high cross-visits with *everyone*
- A Zara with 100k visitors will have more cross-visits than a small boutique, regardless of actual affinity

**Example**: If Store A has 100k visitors and Store B has 10k visitors, we'd expect ~1k cross-visits just by chance (if 10% of mall visitors go to both). If we observe 2k cross-visits, the *lift* is 2x - that's the signal we want.

### 2.2 Computing Lift-Based Affinity

**Lift** measures how much more likely two stores are visited together than expected by chance:

```python
def compute_pairwise_lift(cross_visits_df, fact_stores_df, dim_blocks_df, mall_id):
    """
    Compute lift-based affinity between all store pairs in a mall.

    Lift = Observed Cross-Visits / Expected Cross-Visits
    Expected = (Traffic_A × Traffic_B) / Mall_Total_Traffic

    Args:
        cross_visits_df: DataFrame with store_code_1, store_code_2, total_cross_visits
        fact_stores_df: DataFrame with daily store traffic
        dim_blocks_df: DataFrame with store metadata
        mall_id: Mall to compute lift for

    Returns:
        DataFrame with store_code_1, store_code_2, lift
    """
    # Get stores in this mall
    mall_stores = dim_blocks_df[dim_blocks_df["mall_id"] == mall_id]["store_code"].unique()

    # Aggregate store traffic (sum over all days)
    store_traffic = (
        fact_stores_df[fact_stores_df["store_code"].isin(mall_stores)]
        .groupby("store_code")["people_in"]
        .sum()
        .to_dict()
    )

    # Total mall traffic (sum of all store entries, proxy)
    mall_total = sum(store_traffic.values())

    # Filter cross-visits to this mall
    mall_cross = cross_visits_df[
        cross_visits_df["store_code_1"].isin(mall_stores) &
        cross_visits_df["store_code_2"].isin(mall_stores)
    ].copy()

    # Compute expected cross-visits under independence
    mall_cross["traffic_1"] = mall_cross["store_code_1"].map(store_traffic)
    mall_cross["traffic_2"] = mall_cross["store_code_2"].map(store_traffic)
    mall_cross["expected"] = (
        mall_cross["traffic_1"] * mall_cross["traffic_2"]
    ) / mall_total

    # Compute lift (add small epsilon to avoid division by zero)
    mall_cross["lift"] = mall_cross["total_cross_visits"] / (mall_cross["expected"] + 1)

    return mall_cross[["store_code_1", "store_code_2", "total_cross_visits", "expected", "lift"]]
```

### 2.3 Aggregating to Category-Level Affinity Matrix

**Why aggregate to categories?**
- Store-level affinity is too sparse (most pairs have few cross-visits)
- Category-level patterns are transferable across malls
- We can't know store-level affinity for a *new* store that doesn't exist yet

```python
def build_category_affinity_matrix(cross_visits_df, dim_blocks_df, category_col="bl2_label"):
    """
    Build a category-to-category affinity matrix aggregated across all malls.

    Args:
        cross_visits_df: DataFrame with pairwise cross-visits
        dim_blocks_df: DataFrame with store metadata
        category_col: Which category level to use (bl1_label, bl2_label, bl3_label)

    Returns:
        DataFrame (pivot table) with categories as rows/columns, lift as values
    """
    # Enrich cross-visits with category info
    enriched = (
        cross_visits_df
        .merge(
            dim_blocks_df[["store_code", "mall_id", category_col]].rename(
                columns={"store_code": "store_code_1", category_col: "cat_1", "mall_id": "mall_id_1"}
            ),
            on="store_code_1"
        )
        .merge(
            dim_blocks_df[["store_code", "mall_id", category_col]].rename(
                columns={"store_code": "store_code_2", category_col: "cat_2", "mall_id": "mall_id_2"}
            ),
            on="store_code_2"
        )
    )

    # Keep only same-mall pairs (cross-visits should already be same-mall, but verify)
    enriched = enriched[enriched["mall_id_1"] == enriched["mall_id_2"]]

    # Aggregate to category level
    # Sum cross-visits and compute category-level traffic for expected
    category_cross = (
        enriched
        .groupby(["cat_1", "cat_2"])
        .agg(
            total_cross_visits=("total_cross_visits", "sum"),
            n_pairs=("total_cross_visits", "count"),
        )
        .reset_index()
    )

    # For expected, we need category-level traffic
    category_traffic = (
        dim_blocks_df
        .merge(
            fact_stores_df.groupby("store_code")["people_in"].sum().reset_index(),
            on="store_code"
        )
        .groupby(category_col)["people_in"]
        .sum()
    )

    total_traffic = category_traffic.sum()

    category_cross["traffic_1"] = category_cross["cat_1"].map(category_traffic)
    category_cross["traffic_2"] = category_cross["cat_2"].map(category_traffic)
    category_cross["expected"] = (
        category_cross["traffic_1"] * category_cross["traffic_2"]
    ) / total_traffic

    category_cross["lift"] = category_cross["total_cross_visits"] / (category_cross["expected"] + 1)

    # Pivot to matrix form
    affinity_matrix = category_cross.pivot(index="cat_1", columns="cat_2", values="lift")

    return affinity_matrix
```

### 2.4 Visualizing Category Affinity

```python
import seaborn as sns

def plot_affinity_heatmap(affinity_matrix, title="Category Affinity (Lift)"):
    """Plot heatmap of category affinity matrix."""
    fig, ax = plt.subplots(figsize=(14, 12))

    # Use log scale for better visualization (lift can vary widely)
    import numpy as np
    log_matrix = np.log1p(affinity_matrix.fillna(0))

    sns.heatmap(
        log_matrix,
        cmap="RdYlGn",
        center=0,
        ax=ax,
        square=True,
        cbar_kws={"label": "log(1 + Lift)"}
    )
    ax.set_title(title)
    plt.tight_layout()
    return fig
```

### Deliverables
- [ ] `src/synergy/lift.py`: Functions to compute pairwise lift
- [ ] `src/synergy/affinity_matrix.py`: Category affinity matrix builder
- [ ] Affinity heatmaps at bl1, bl2, bl3 levels
- [ ] Analysis of highest/lowest affinity category pairs

---

## Phase 3: Store Performance Modeling (Layer 2)

### 3.1 Defining the Prediction Target

**What are we predicting?**

We model three key performance metrics:

| Target | Formula | Interpretation |
|--------|---------|----------------|
| `capture_rate` | `people_in / people_window_flow` | Conversion efficiency |
| `sales_per_sqm` | `sales_r12m / gla` | Revenue efficiency |
| `dwell_time` | `store_average_dwell_time` | Engagement |

**Why multiple targets?**
- Different use cases require different objectives
- Some stores have high traffic but low sales (and vice versa)
- Multi-target modeling reveals trade-offs

### 3.2 Feature Engineering

**Feature Categories**:

```python
def engineer_store_features(store_code, dim_blocks_df, fact_stores_df,
                            cross_visits_df, affinity_matrix, category_col="bl2_label"):
    """
    Engineer features for a single store.

    Returns dict of features for use in prediction model.
    """
    store_info = dim_blocks_df[dim_blocks_df["store_code"] == store_code].iloc[0]
    mall_id = store_info["mall_id"]
    store_category = store_info[category_col]

    features = {}

    # === STORE INTRINSIC FEATURES ===
    # These are characteristics of the store itself
    features["gla"] = store_info["gla"]
    features["gla_category"] = store_info["gla_category"]  # Small/Medium/Large
    features["bl1_label"] = store_info["bl1_label"]
    features["bl2_label"] = store_info["bl2_label"]

    # === LOCATION QUALITY FEATURES ===
    # Window flow is a proxy for how "prime" the location is
    store_daily = fact_stores_df[fact_stores_df["store_code"] == store_code]
    features["avg_window_flow"] = store_daily["people_window_flow"].mean()
    features["median_window_flow"] = store_daily["people_window_flow"].median()

    # === NEIGHBORHOOD SYNERGY FEATURES ===
    # How well does this store's category synergize with its actual neighbors?

    # Get this store's cross-visit partners
    store_cross = cross_visits_df[
        (cross_visits_df["store_code_1"] == store_code) |
        (cross_visits_df["store_code_2"] == store_code)
    ]

    # Get neighbor categories
    neighbor_codes = set(store_cross["store_code_1"]) | set(store_cross["store_code_2"])
    neighbor_codes.discard(store_code)

    neighbor_categories = (
        dim_blocks_df[dim_blocks_df["store_code"].isin(neighbor_codes)]
        [category_col]
        .value_counts()
    )

    # Compute synergy score: sum of (affinity × neighbor_count) for each neighbor category
    synergy_score = 0
    for neighbor_cat, count in neighbor_categories.items():
        if store_category in affinity_matrix.index and neighbor_cat in affinity_matrix.columns:
            affinity = affinity_matrix.loc[store_category, neighbor_cat]
            if pd.notna(affinity):
                synergy_score += affinity * count

    features["neighborhood_synergy"] = synergy_score
    features["n_neighbors"] = len(neighbor_codes)

    # === MALL CONTEXT FEATURES ===
    mall_stores = dim_blocks_df[dim_blocks_df["mall_id"] == mall_id]
    features["mall_total_gla"] = mall_stores["gla"].sum()
    features["mall_n_stores"] = len(mall_stores)
    features["mall_category_share"] = (
        mall_stores[mall_stores[category_col] == store_category]["gla"].sum()
        / features["mall_total_gla"]
    )

    return features
```

### 3.3 Building the Training Dataset

**Critical**: Aggregate to store-level, not day-level.

**Why?**
- Day-level creates pseudo-replication (same store appears 365 times)
- Temporal autocorrelation violates independence assumption
- We want to predict *store* performance, not *day* performance

```python
def build_training_dataset(dim_blocks_df, fact_stores_df, store_financials_df,
                           cross_visits_df, affinity_matrix):
    """
    Build training dataset at store level.

    Returns:
        X: Feature DataFrame
        y: Target DataFrame (capture_rate, sales_per_sqm, dwell_time)
    """
    # Aggregate daily metrics to store level
    store_agg = (
        fact_stores_df
        .groupby("store_code")
        .agg(
            total_people_in=("people_in", "sum"),
            total_window_flow=("people_window_flow", "sum"),
            avg_dwell_time=("store_average_dwell_time", "mean"),
            n_days=("date", "nunique"),
        )
        .reset_index()
    )

    # Compute targets
    store_agg["capture_rate"] = store_agg["total_people_in"] / store_agg["total_window_flow"]

    # Join financial data
    store_agg = store_agg.merge(
        store_financials_df.rename(columns={"codstr": "store_code"}),
        on="store_code",
        how="left"
    )

    # Join GLA for sales_per_sqm
    store_agg = store_agg.merge(
        dim_blocks_df[["store_code", "gla"]],
        on="store_code"
    )
    store_agg["sales_per_sqm"] = store_agg["sales_r12m"] / store_agg["gla"]

    # Engineer features for each store
    feature_records = []
    for store_code in store_agg["store_code"]:
        features = engineer_store_features(
            store_code, dim_blocks_df, fact_stores_df,
            cross_visits_df, affinity_matrix
        )
        features["store_code"] = store_code
        feature_records.append(features)

    X = pd.DataFrame(feature_records).set_index("store_code")
    y = store_agg.set_index("store_code")[["capture_rate", "sales_per_sqm", "avg_dwell_time"]]

    # Align indices
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    return X, y
```

### 3.4 Model Training with Proper Cross-Validation

**Why leave-one-mall-out CV?**
- Tests transferability: can we predict for a mall we haven't seen?
- Prevents data leakage from same-mall patterns
- More realistic for the swap use case (new store = unseen scenario)

```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, LeaveOneGroupOut
from sklearn.preprocessing import LabelEncoder
import numpy as np

def train_performance_model(X, y, target_col, mall_ids):
    """
    Train a performance prediction model with leave-one-mall-out CV.

    Args:
        X: Feature DataFrame
        y: Target DataFrame
        target_col: Which target to predict ('capture_rate', 'sales_per_sqm', 'avg_dwell_time')
        mall_ids: Series mapping store_code to mall_id

    Returns:
        Trained model, CV scores
    """
    # Encode categorical features
    X_encoded = X.copy()
    cat_cols = X.select_dtypes(include=['object']).columns
    encoders = {}
    for col in cat_cols:
        le = LabelEncoder()
        X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
        encoders[col] = le

    # Prepare target
    y_target = y[target_col].dropna()
    X_encoded = X_encoded.loc[y_target.index]
    groups = mall_ids.loc[y_target.index]

    # Model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )

    # Leave-one-mall-out CV
    logo = LeaveOneGroupOut()
    cv_scores = cross_val_score(
        model, X_encoded, y_target,
        cv=logo, groups=groups,
        scoring='r2'
    )

    print(f"Target: {target_col}")
    print(f"CV R² scores by mall: {cv_scores}")
    print(f"Mean R²: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    # Fit final model on all data
    model.fit(X_encoded, y_target)

    return model, encoders, cv_scores
```

### 3.5 Feature Importance Analysis

```python
def analyze_feature_importance(model, feature_names):
    """Analyze and plot feature importance from trained model."""
    importance = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 8))
    importance.head(15).plot.barh(x='feature', y='importance', ax=ax)
    ax.set_title("Feature Importance (Top 15)")
    ax.invert_yaxis()

    return importance, fig
```

### Deliverables
- [ ] `src/models/performance_model.py`: Performance prediction model
- [ ] `src/features/store_features.py`: Feature engineering functions
- [ ] Model evaluation report (CV scores, feature importance)
- [ ] Analysis of prediction errors (which stores are hardest to predict?)

---

## Phase 4: Swap Simulation Engine (Layer 3)

### 4.1 The Swap Simulation Algorithm

**Core insight**: A swap is not just about the new store - it changes the graph, which affects all neighbors.

```python
class SwapSimulator:
    """
    Simulate the impact of replacing one store with another category.

    The simulator:
    1. Computes baseline mall score
    2. Removes old store and re-predicts neighbor performance (they lose synergy)
    3. Adds new store and predicts its performance
    4. Re-predicts neighbor performance (they gain synergy)
    5. Computes new mall score
    """

    def __init__(self, dim_blocks, fact_stores, cross_visits,
                 affinity_matrix, performance_model, encoders):
        self.dim_blocks = dim_blocks
        self.fact_stores = fact_stores
        self.cross_visits = cross_visits
        self.affinity_matrix = affinity_matrix
        self.performance_model = performance_model
        self.encoders = encoders

    def simulate_swap(self, mall_id, old_store_code, new_category, new_gla=None):
        """
        Simulate replacing old_store_code with a store of new_category.

        Args:
            mall_id: Mall where swap occurs
            old_store_code: Store to remove
            new_category: BL2 category of new store
            new_gla: GLA of new store (defaults to old store's GLA)

        Returns:
            dict with baseline_score, new_score, delta, breakdown
        """
        # Get old store info
        old_store = self.dim_blocks[
            self.dim_blocks["store_code"] == old_store_code
        ].iloc[0]

        if new_gla is None:
            new_gla = old_store["gla"]

        # === STEP 1: Compute baseline ===
        baseline = self._compute_mall_performance(mall_id)

        # === STEP 2: Identify affected neighbors ===
        # Stores that have cross-visits with the old store
        affected_stores = self._get_neighbors(old_store_code)

        # === STEP 3: Estimate new store's synergy with neighbors ===
        new_store_synergy = self._estimate_synergy_for_new_store(
            mall_id, new_category, affected_stores
        )

        # === STEP 4: Predict new store performance ===
        new_store_features = self._build_new_store_features(
            mall_id, new_category, new_gla, new_store_synergy
        )
        new_store_performance = self._predict_performance(new_store_features)

        # === STEP 5: Re-predict neighbor performance ===
        # Neighbors lose synergy with old store, gain synergy with new store
        neighbor_deltas = self._compute_neighbor_deltas(
            affected_stores, old_store["bl2_label"], new_category
        )

        # === STEP 6: Compute new mall score ===
        new_mall_performance = self._compute_new_mall_performance(
            mall_id, old_store_code, new_store_performance, neighbor_deltas
        )

        return {
            "baseline": baseline,
            "new": new_mall_performance,
            "delta": new_mall_performance["score"] - baseline["score"],
            "new_store_prediction": new_store_performance,
            "affected_neighbors": len(affected_stores),
            "neighbor_impact": sum(neighbor_deltas.values()),
        }

    def _estimate_synergy_for_new_store(self, mall_id, new_category, neighbor_stores):
        """
        Estimate synergy score for a new store based on its category and neighbors.

        Uses the category affinity matrix to predict how the new store
        would connect to existing stores.
        """
        synergy = 0
        for neighbor_code in neighbor_stores:
            neighbor_cat = self.dim_blocks[
                self.dim_blocks["store_code"] == neighbor_code
            ]["bl2_label"].iloc[0]

            # Look up affinity between new category and neighbor category
            if (new_category in self.affinity_matrix.index and
                neighbor_cat in self.affinity_matrix.columns):
                affinity = self.affinity_matrix.loc[new_category, neighbor_cat]
                if pd.notna(affinity):
                    synergy += affinity

        return synergy

    def _get_neighbors(self, store_code):
        """Get stores that have cross-visits with given store."""
        cross = self.cross_visits[
            (self.cross_visits["store_code_1"] == store_code) |
            (self.cross_visits["store_code_2"] == store_code)
        ]
        neighbors = set(cross["store_code_1"]) | set(cross["store_code_2"])
        neighbors.discard(store_code)
        return list(neighbors)

    # ... additional helper methods ...
```

### 4.2 Second-Order Effects: The Key Differentiator

**Why second-order effects matter**:

When you swap a store, neighbors are affected:
- They lose cross-visit synergy with the old store
- They gain cross-visit synergy with the new store
- This changes their "neighborhood_synergy" feature
- Which changes their predicted performance

```python
def _compute_neighbor_deltas(self, neighbor_stores, old_category, new_category):
    """
    Compute performance change for each neighbor due to the swap.

    The intuition:
    - If old store was high-affinity with neighbor, removing it hurts neighbor
    - If new store is high-affinity with neighbor, adding it helps neighbor
    """
    deltas = {}

    for neighbor_code in neighbor_stores:
        neighbor_cat = self.dim_blocks[
            self.dim_blocks["store_code"] == neighbor_code
        ]["bl2_label"].iloc[0]

        # Affinity lost (old store removed)
        old_affinity = self.affinity_matrix.get((neighbor_cat, old_category), 0)

        # Affinity gained (new store added)
        new_affinity = self.affinity_matrix.get((neighbor_cat, new_category), 0)

        # Net change in neighbor's synergy score
        synergy_delta = new_affinity - old_affinity

        # Translate synergy delta to performance delta
        # (This requires understanding the model's sensitivity to synergy)
        # Approximation: use model's feature importance for neighborhood_synergy
        performance_delta = synergy_delta * self.synergy_coefficient

        deltas[neighbor_code] = performance_delta

    return deltas
```

### 4.3 Uncertainty Quantification

**Why uncertainty matters for business decisions**:
- Swapping a tenant is a major decision (lease terms, fit-out costs)
- Point estimates are not enough - URW needs confidence intervals
- High uncertainty → gather more data or choose safer option

```python
def simulate_swap_with_uncertainty(self, mall_id, old_store_code, new_category,
                                    n_simulations=100):
    """
    Run swap simulation with uncertainty estimation via bootstrap.

    Returns point estimate + confidence interval.
    """
    results = []

    for i in range(n_simulations):
        # Add noise to affinity estimates (bootstrap-like)
        noisy_affinity = self.affinity_matrix * np.random.normal(1, 0.1,
                                                                  self.affinity_matrix.shape)

        # Run simulation with noisy affinity
        result = self.simulate_swap(
            mall_id, old_store_code, new_category,
            affinity_override=noisy_affinity
        )
        results.append(result["delta"])

    return {
        "mean_delta": np.mean(results),
        "std_delta": np.std(results),
        "ci_lower": np.percentile(results, 5),
        "ci_upper": np.percentile(results, 95),
        "prob_positive": np.mean([r > 0 for r in results]),
    }
```

### Deliverables
- [ ] `src/simulation/swap_engine.py`: SwapSimulator class
- [ ] `src/simulation/uncertainty.py`: Uncertainty quantification
- [ ] Validation: Test on "pseudo-swaps" using temporal holdout
- [ ] Documentation of assumptions and limitations

---

## Phase 5: Recommendation Engine

### 5.1 Identifying Swap Candidates

**Two approaches**:

1. **Bottom-up**: Find underperforming stores, suggest replacements
2. **Top-down**: Given strategic goals, find optimal swaps

```python
def identify_underperformers(store_performance, dim_blocks, threshold_percentile=25):
    """
    Identify stores performing below their category benchmark.

    A store is an underperformer if its capture_rate (or other metric)
    is below the 25th percentile for its category.
    """
    # Merge performance with category
    perf_with_cat = store_performance.merge(
        dim_blocks[["store_code", "bl2_label", "mall_id"]],
        on="store_code"
    )

    # Compute category benchmarks
    category_benchmarks = (
        perf_with_cat
        .groupby("bl2_label")["capture_rate"]
        .quantile(threshold_percentile / 100)
    )

    # Flag underperformers
    perf_with_cat["category_benchmark"] = perf_with_cat["bl2_label"].map(category_benchmarks)
    perf_with_cat["is_underperformer"] = (
        perf_with_cat["capture_rate"] < perf_with_cat["category_benchmark"]
    )

    return perf_with_cat[perf_with_cat["is_underperformer"]]


def suggest_replacement_categories(mall_id, old_store_code, dim_blocks,
                                   affinity_matrix, top_k=5):
    """
    Suggest categories that would have high synergy with the store's neighbors.

    Logic:
    1. Get neighbors of the store to be replaced
    2. For each candidate category, compute expected synergy
    3. Rank by synergy and filter out categories already over-represented
    """
    # Get neighbor categories
    neighbors = get_neighbors(old_store_code, cross_visits)
    neighbor_cats = dim_blocks[dim_blocks["store_code"].isin(neighbors)]["bl2_label"]

    # Score each candidate category
    candidate_scores = {}
    for candidate_cat in affinity_matrix.index:
        score = 0
        for neighbor_cat in neighbor_cats:
            if neighbor_cat in affinity_matrix.columns:
                affinity = affinity_matrix.loc[candidate_cat, neighbor_cat]
                if pd.notna(affinity):
                    score += affinity
        candidate_scores[candidate_cat] = score

    # Sort and return top-k
    ranked = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
```

### 5.2 Multi-Swap Optimization

**For strategic planning**: Find the best set of swaps to maximize improvement.

```python
def optimize_multiple_swaps(mall_id, max_swaps=3, objective_weights=None):
    """
    Find optimal set of swaps using greedy search.

    Note: Full combinatorial optimization is NP-hard, so we use greedy.
    """
    if objective_weights is None:
        objective_weights = {
            'revenue': 0.4,
            'traffic': 0.3,
            'sustainability': 0.2,
            'diversity': 0.1,
        }

    current_state = get_current_mall_state(mall_id)
    swaps_made = []

    for _ in range(max_swaps):
        # Find all candidate swaps
        candidates = []
        underperformers = identify_underperformers(current_state)

        for store in underperformers:
            replacement_cats = suggest_replacement_categories(mall_id, store)
            for new_cat, _ in replacement_cats:
                sim_result = simulator.simulate_swap(mall_id, store, new_cat)
                candidates.append({
                    'old_store': store,
                    'new_category': new_cat,
                    'delta': sim_result['delta'],
                    'full_result': sim_result,
                })

        # Select best swap
        if not candidates:
            break

        best_swap = max(candidates, key=lambda x: x['delta'])

        if best_swap['delta'] <= 0:
            break  # No more beneficial swaps

        swaps_made.append(best_swap)
        # Update current state for next iteration
        current_state = apply_swap(current_state, best_swap)

    return swaps_made
```

### Deliverables
- [ ] `src/recommendations/underperformers.py`: Underperformer identification
- [ ] `src/recommendations/swap_suggestions.py`: Category recommendation logic
- [ ] `src/recommendations/optimizer.py`: Multi-swap optimization
- [ ] Recommendation explainability (why this swap?)

---

## Phase 6: Streamlit Dashboard

### 6.1 Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NAVIGATION                              │
│  [Mall Overview] [Store Explorer] [Swap Simulator] [Recommend]  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ MALL OVERVIEW                                                   │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │  Footfall   │ │   Revenue   │ │ Dwell Time  │ │    SRI      ││
│ │   150,000   │ │   €2.5M     │ │   65 min    │ │     72      ││
│ │   +5.2%     │ │   +8.3%     │ │   -2.1%     │ │   +3.0%     ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                                                                 │
│ [Category Mix Pie Chart]     [Synergy Network Graph]           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ SWAP SIMULATOR                                                  │
│                                                                 │
│ Select Store to Replace: [Dropdown: Store List]                │
│ Select New Category:     [Dropdown: Category List]             │
│                                                                 │
│ [SIMULATE SWAP]                                                │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ RESULTS                                                      ││
│ │                                                              ││
│ │ Mall Score:  72.3 → 74.1  (+1.8, 95% CI: [0.9, 2.7])       ││
│ │ Revenue:     €2.5M → €2.6M                                  ││
│ │ Neighbors Affected: 12 stores                               ││
│ │ Confidence: 87% probability of improvement                  ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Key Streamlit Components

```python
# src/streamlit_app.py

import streamlit as st
import pandas as pd
from simulation.swap_engine import SwapSimulator
from visualization.network import plot_synergy_network

st.set_page_config(page_title="URW Retail Mix Optimizer", layout="wide")

# Sidebar: Mall Selection
st.sidebar.title("Mall Selection")
mall_id = st.sidebar.selectbox("Select Mall", options=mall_list)

# Load data for selected mall
mall_data = load_mall_data(mall_id)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Mall Overview", "Store Explorer", "Swap Simulator", "Recommendations"
])

with tab1:
    st.header(f"Mall Overview: {mall_names[mall_id]}")

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Footfall", f"{mall_data['footfall']:,}",
                  delta=f"{mall_data['footfall_delta']:+.1f}%")
    # ... more KPIs ...

    # Category mix
    st.subheader("Category Mix")
    fig_pie = plot_category_pie(mall_data)
    st.plotly_chart(fig_pie)

with tab3:
    st.header("Swap Simulator")

    col1, col2 = st.columns(2)
    with col1:
        old_store = st.selectbox("Store to Replace",
                                  options=mall_data['stores'])
    with col2:
        new_category = st.selectbox("New Category",
                                     options=category_list)

    if st.button("Simulate Swap"):
        with st.spinner("Running simulation..."):
            result = simulator.simulate_swap_with_uncertainty(
                mall_id, old_store, new_category
            )

        st.success("Simulation complete!")

        # Display results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Mall Score Change",
                     f"{result['mean_delta']:+.2f}",
                     delta=f"95% CI: [{result['ci_lower']:.2f}, {result['ci_upper']:.2f}]")
        with col2:
            st.metric("Probability of Improvement",
                     f"{result['prob_positive']:.0%}")
        with col3:
            st.metric("Neighbors Affected",
                     f"{result['n_neighbors']}")
```

### Deliverables
- [ ] `src/streamlit_app.py`: Main dashboard application
- [ ] `src/visualization/`: Plotting functions (network, heatmaps, KPIs)
- [ ] User guide for dashboard

---

## Phase 7: Validation & Documentation

### 7.1 Validation Strategy

**The fundamental challenge**: We can't observe counterfactuals.

**Approaches**:

1. **Temporal holdout**:
   - Train on months 1-9, test on months 10-12
   - Pretend month 10 is "new" and predict performance

2. **Leave-one-mall-out**:
   - Train on 21 malls, predict for 1 mall
   - Tests transferability

3. **Pseudo-swaps**:
   - Find cases where a store changed category (if any in data)
   - Compare predicted vs actual impact

4. **Sensitivity analysis**:
   - How much do predictions change with small input changes?
   - Identifies fragile vs robust recommendations

```python
def validate_with_temporal_holdout(fact_stores, train_end_date, test_start_date):
    """
    Validate model using temporal split.

    Train on data before train_end_date, test on data after test_start_date.
    """
    train_data = fact_stores[fact_stores["date"] < train_end_date]
    test_data = fact_stores[fact_stores["date"] >= test_start_date]

    # Build features and train model on training period
    X_train, y_train = build_training_dataset(train_data, ...)
    model, encoders = train_performance_model(X_train, y_train, ...)

    # Evaluate on test period
    X_test, y_test = build_training_dataset(test_data, ...)
    y_pred = model.predict(X_test)

    # Metrics
    from sklearn.metrics import r2_score, mean_absolute_error
    print(f"Temporal holdout R²: {r2_score(y_test, y_pred):.3f}")
    print(f"Temporal holdout MAE: {mean_absolute_error(y_test, y_pred):.3f}")
```

### 7.2 Limitations to Document

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Cross-visits are historical | New store's actual cross-visits may differ | Use confidence intervals |
| Financial data incomplete | Can't validate sales predictions for all stores | Validate on subset with data |
| 22 malls may not generalize | Patterns might not transfer to new markets | Focus on methodology over results |
| No causal identification | Correlation ≠ causation for synergy → performance | Be explicit about assumptions |
| Static affinity matrix | Affinity patterns may change over time | Recommend periodic recalibration |

### Deliverables
- [ ] Validation report with metrics
- [ ] Sensitivity analysis results
- [ ] Limitations and assumptions document
- [ ] Technical documentation for handover

---

## Timeline (2 Weeks)

| Days | Phase | Key Activities | Deliverables |
|------|-------|----------------|--------------|
| 1-2 | Phase 1 | Data loading, quality checks, initial EDA | Data quality report |
| 3-4 | Phase 2 | Lift computation, category affinity matrix | Affinity heatmaps |
| 5-6 | Phase 3 | Feature engineering, performance model training | Trained model, CV report |
| 7-8 | Phase 4 | Swap simulator implementation | Working simulator |
| 9-10 | Phase 5 | Recommendation engine, optimization | Recommendation logic |
| 11-12 | Phase 6 | Streamlit dashboard | Interactive demo |
| 13-14 | Phase 7 | Validation, documentation, presentation | Final deliverables |

---

## File Structure

```
src/
├── __init__.py
├── constants/
│   ├── constants.py       # Global constants (CSV params, etc.)
│   └── paths.py           # File paths
├── data/
│   ├── loader.py          # Data loading functions
│   └── quality.py         # Data quality checks
├── synergy/
│   ├── lift.py            # Pairwise lift computation
│   ├── affinity_matrix.py # Category affinity matrix
│   └── graph.py           # NetworkX graph utilities
├── features/
│   ├── store_features.py  # Store-level feature engineering
│   └── mall_features.py   # Mall-level feature engineering
├── models/
│   ├── performance_model.py  # Performance prediction model
│   └── evaluation.py         # Model evaluation utilities
├── simulation/
│   ├── swap_engine.py     # SwapSimulator class
│   └── uncertainty.py     # Uncertainty quantification
├── recommendations/
│   ├── underperformers.py # Underperformer identification
│   ├── swap_suggestions.py # Category recommendations
│   └── optimizer.py       # Multi-swap optimization
├── visualization/
│   ├── network.py         # Network visualizations
│   ├── heatmaps.py        # Affinity heatmaps
│   └── kpis.py            # KPI cards and charts
└── streamlit_app.py       # Main Streamlit application

notebooks/
├── 01_eda.ipynb           # Exploratory data analysis
├── 02_synergy.ipynb       # Synergy analysis
├── 03_performance_model.ipynb  # Model development
├── 04_simulation.ipynb    # Simulation testing
└── 05_validation.ipynb    # Validation experiments

docs/
├── ROADMAP.md             # This file
├── DATA_DICTIONARY.md     # Data documentation
└── METHODOLOGY.md         # Technical methodology
```

---

## Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| **Model Performance** | Leave-one-mall-out R² | > 0.3 |
| **Simulation Validity** | Temporal holdout accuracy | > 0.25 R² |
| **Recommendation Quality** | % swaps with positive predicted delta | > 70% |
| **Uncertainty Calibration** | 95% CI coverage | ~95% |
| **Dashboard Usability** | Complete swap simulation in < 10 seconds | Yes |

---

## Next Steps

1. [x] Pull data with `dvc pull`
2. [ ] Run Phase 1 data quality checks
3. [ ] Complete EDA notebook
4. [ ] Begin Layer 1 (synergy quantification)
