# URW x HEC Data Challenge - Project Roadmap

## Project Goal

**Design a data-driven framework to assess, simulate, and recommend optimal retail mixes** that maximize the overall value of URW shopping centers in terms of revenue, visitor engagement, efficiency, and future-readiness.

The primary deliverable is a **robust analytical approach** with clear justification, not just raw results.

### Key Business Questions

1. What is the "ideal" tenant composition for a given mall profile?
2. How does adding, removing, or relocating a tenant impact others and the mall as a whole?
3. How can URW proactively adapt the retail mix to emerging trends?

---

## Our Approach

### Core Deliverables

1. **KPI Dashboard**: Interactive visualization showing:
   - **Mall-level KPIs**: Average dwell time, foot traffic, average money spent, average SRI score
   - **Store-level KPIs**: OCR (Occupancy Cost Ratio), average dwell time, capture rate, sales per sqm

2. **Optimal Tenant Mix Model**: Given an empty mall profile (total GLA, number of blocks, location), determine the ideal tenant composition that maximizes our composite performance metric

3. **Impact Simulation Model**: Compute the effect of adding or removing a store on mall performance and neighboring stores

4. **Pareto Optimization (Stretch Goal)**: Multi-objective optimization showing trade-offs between metrics rather than a single composite score (e.g., "this mix optimizes X but costs Y on metric Z")

### Key Design Decision: Retailer-Level Synergy

We compute synergy metrics at the **retailer level** (using `retailer_code` from `fact_stores`), not physical store level. This allows us to:
- Generalize patterns across malls
- Recommend retailer types rather than specific store instances
- Build transferable models for empty mall profiles

---

## KPIs and Metrics Framework

### Store-Level Metrics (Dashboard)

Individual store performance metrics displayed in the dashboard for drill-down analysis.

| Metric | Description | Data Source |
|--------|-------------|-------------|
| **Capture Rate** | `people_in / people_window_flow` | `fact_stores_v1` |
| **Sales per sqm** | `sales_r12m / gla` | `store_financials_v1`, `dim_blocks_v1` |
| **Occupancy Cost Ratio (OCR)** | `total_costs_r12m / sales_r12m` | `store_financials_v1` |
| **Store Dwell Time** | Time spent inside store | `fact_stores_v1.store_average_dwell_time` |
| **Cross-Visit Index** | Avg co-visits with other stores | `cross_visits_v1` |
| **Sustainability Score** | SRI rating | `fact_sri_scores_v1.sri_score` |

### Mall-Level Metrics (Dashboard & Optimization)

Mall-level metrics come from two sources:
1. **Direct metrics**: Measured at the mall level
2. **Aggregated metrics**: Store-level metrics rolled up to mall level

#### Direct Mall Metrics

| Metric | Description | Data Source |
|--------|-------------|-------------|
| **Total Footfall** | Daily/monthly visitor count | `fact_malls_v1.people_in` |
| **Mall Dwell Time** | Average time spent in mall | `fact_malls_v1.average_dwell_time` |
| **Occupancy Rate** | Leased GLA / Total GLA | `dim_blocks_v1` |

#### Aggregated from Store Metrics

| Mall Metric | Aggregation Method | Source Store Metric |
|-------------|-------------------|---------------------|
| **Avg Sales Density** | Mean of store sales/sqm | Sales per sqm |
| **Avg OCR** | Mean (or GLA-weighted) | OCR |
| **% Healthy Tenants** | % stores with OCR < threshold | OCR |
| **Avg SRI Score** | Mean (or GLA-weighted) | SRI score |
| **Avg Capture Rate** | Mean across stores | Capture rate |

### Retail Mix Quality Metrics (Mall-Level)

These metrics characterize the tenant mix composition.

| Metric | Description | Purpose |
|--------|-------------|---------|
| **Category Diversity Index** | Shannon entropy of BL1/BL2 categories | Measure tenant variety |
| **Anchor-Satellite Ratio** | Large stores vs small/medium | Balance of traffic drivers |
| **Synergy Score** | Aggregate cross-visit strength of tenant mix | Measure tenant complementarity |
| **Sustainability Mix Score** | Weighted avg SRI of tenant base | ESG readiness |

### Mall-Level Composite Score (Optimization Objective)

The optimization model maximizes a **mall-level composite score** that combines:

```
Composite Score = w1 * Revenue Component
                + w2 * Traffic Component
                + w3 * Tenant Health Component
                + w4 * Synergy Component
                + w5 * Sustainability Component
                + w6 * Diversity Component
```

| Component | Built From | Notes |
|-----------|-----------|-------|
| **Revenue** | Avg sales density, total sales | Primary business metric |
| **Traffic** | Footfall, mall dwell time | Visitor engagement |
| **Tenant Health** | Avg OCR, % healthy tenants | Financial sustainability of tenants |
| **Synergy** | Aggregate cross-visit strength | How well tenants complement each other |
| **Sustainability** | Avg SRI score | ESG alignment |
| **Diversity** | Category entropy | Risk mitigation through variety |

Weights (w1-w6) can be adjusted based on URW's strategic priorities.

---

## Phase 1: Data Foundation & Exploration (COMPLETED)

### 1.1 Data Ingestion & Quality Assessment
- [x] Load all datasets and verify schema against data dictionary
- [x] Profile data: missing values, outliers, distributions
- [x] Validate joins between tables (store_code, mall_id)
- [x] Document data quality issues and coverage gaps

### 1.2 Exploratory Data Analysis (EDA)
- [x] **Mall profiles**: Compare Vélizy 2, Parly 2, Euralille on size, footfall, category mix
- [x] **Temporal patterns**: Day-of-week, seasonality in footfall (autocorrelation analysis)
- [x] **Category analysis**: Distribution by BL1/BL2/BL3 categories per mall
- [x] **Store counts**: Number of retailers and categories per mall

### Deliverables
- [x] EDA notebook (`notebooks/eda.ipynb`)

---

## Phase 2: Synergy Metric Development (IN PROGRESS)

### 2.1 Cross-Visit Network Analysis
- [ ] Build retailer co-visitation graph from `cross_visits_v1`
- [ ] Aggregate cross-visits by retailer (not physical store)
- [ ] Compute network metrics:
  - Degree centrality (traffic hubs)
  - Betweenness centrality (bridge retailers)
  - Community detection (natural retailer clusters)

### 2.2 Synergy Score Computation
- [ ] Define pairwise synergy between retailers based on cross-visits
- [ ] Normalize by store traffic to avoid size bias
- [ ] Create retailer affinity matrix
- [ ] Aggregate to category level (BL2/BL3) for pattern identification

### 2.3 Category Affinity Analysis
- [ ] Build category affinity heatmap
- [ ] Identify complementary vs. competing categories
- [ ] Quantify cannibalization risk between similar retailers

### Deliverables
- [ ] Synergy metric notebook (`notebooks/synergy.ipynb`)
- [ ] Retailer affinity matrix
- [ ] Category-level synergy patterns

---

## Phase 3: Mall-Level Composite Score

### 3.1 Store Metric Computation
Compute store-level metrics for all stores:
- [ ] Sales per sqm (join `store_financials` with `dim_blocks`)
- [ ] OCR (from `store_financials`)
- [ ] Capture rate (from `fact_stores`)
- [ ] Store dwell time (from `fact_stores`)
- [ ] SRI score (from `fact_sri_scores`)

### 3.2 Mall-Level Aggregation
Roll up store metrics to mall level:
- [ ] Define aggregation methods (mean, weighted mean, percentiles)
- [ ] Compute direct mall metrics (footfall, dwell time)
- [ ] Compute aggregated metrics (avg OCR, avg sales density, etc.)
- [ ] Compute mix quality metrics (diversity index, synergy score)

### 3.3 Composite Score Definition
- [ ] Normalize all components to comparable scales (0-1 or z-scores)
- [ ] Define initial weights for each component
- [ ] Validate composite score against intuition (do "good" malls score high?)
- [ ] Sensitivity analysis on weight choices

### 3.4 Store-Level Benchmarking (Dashboard Support)
- [ ] Normalize store metrics within categories for fair comparison
- [ ] Identify over/under-performers relative to category benchmarks
- [ ] Flag stores contributing negatively to mall composite

### Deliverables
- [ ] Mall composite score methodology
- [ ] Store benchmarking for dashboard

---

## Phase 4: Optimization Framework

### 4.1 Mall Profile Definition
A mall profile consists of:
- **Total GLA**: Total leasable area
- **Number of blocks**: Available store slots
- **Location**: Country/region (affects category preferences)

### 4.2 Tenant Mix Optimization Model
Given a mall profile, optimize:
- **Objective**: Maximize composite performance metric
- **Decision variables**: Number of stores per category (BL2 level)
- **Constraints**:
  - Total GLA constraint
  - Min/max stores per category
  - Anchor store requirements
  - Category diversity minimum

### 4.3 Impact Simulation Engine
For existing malls, simulate:
- **Tenant addition**: Predict impact on overall mall performance and synergy
- **Tenant removal**: Estimate traffic/sales loss and redistribution
- **Tenant swap**: Model replacement of one retailer type with another

### 4.4 Pareto Optimization (Stretch Goal)
Multi-objective optimization across:
1. Revenue (total sales)
2. Traffic (footfall)
3. Sustainability (SRI)
4. Diversity (category entropy)

Output: Pareto frontier showing optimal trade-offs

### Deliverables
- [ ] Optimization model specification
- [ ] Simulation engine (Python module)
- [ ] Pareto frontier visualization (if time permits)

---

## Phase 5: Dashboard & Delivery

### 5.1 Streamlit Dashboard
Interactive application with:
- **Mall Overview**: KPIs, category breakdown, sustainability score
- **Store Explorer**: Performance metrics, synergy network
- **What-If Simulator**: Add/remove tenants and see impact
- **Recommendations Panel**: Suggested optimizations with rationale

### 5.2 Final Presentation
- Executive summary of methodology
- Key insights from the data
- Framework demonstration
- Strategic recommendations for URW
- Limitations and future directions

### Deliverables
- [ ] Streamlit app
- [ ] Presentation deck
- [ ] Technical documentation

---

## Technical Approach

### Graph Analysis (Phase 2)
- NetworkX for co-visitation graph
- Community detection (Louvain algorithm)
- Centrality measures for retailer importance

### Machine Learning (Phase 3)
- Regression for performance prediction
- Clustering for retailer segmentation

### Optimization (Phase 4)
- Linear/Mixed Integer Programming for GLA allocation
- Multi-objective optimization (NSGA-II) for Pareto frontier
- Constraint satisfaction for feasibility

### Visualization (Phase 5)
- Plotly for interactive charts
- Streamlit for dashboard
- NetworkX + Plotly for synergy network visualization

---

## Data Mapping

### Key Joins

```
dim_blocks.store_code -> fact_stores.store_code
dim_blocks.store_code -> store_financials.codestr
dim_blocks.store_code -> fact_sri_scores.store_code
dim_blocks.store_code -> cross_visits.store_code_1 / store_code_2
dim_blocks.mall_id -> fact_malls.mall_id
dim_blocks.mall_id -> dim_malls.id
```

### Retailer Aggregation
For synergy analysis, aggregate from `store_code` to `retailer_code`:
- Cross-visits: Sum visits between all stores of retailer pairs
- Performance: Average metrics across retailer's stores

---

## Risk Factors & Mitigations

| Risk | Mitigation |
|------|------------|
| Incomplete financial data | Use available stores as benchmarks; impute by category |
| Cross-visit data sparsity | Aggregate to retailer/category level for robust patterns |
| Limited mall sample (3 named malls) | Focus on transferable methodology over mall-specific results |
| Short timeframe | Prioritize core deliverables; Pareto optimization is stretch goal |

---

## Success Criteria

The solution will be evaluated on:

1. **Analytical Rigor**: Sound methodology with clear justification
2. **Business Relevance**: Actionable insights for URW decision-makers
3. **Innovation**: Creative use of available data and techniques
4. **Presentation**: Clear communication of approach and findings
5. **Bonus**: Streamlit interface and sustainability integration

---

## Current Status

- **Phase 1**: COMPLETED - EDA notebook done
- **Phase 2**: IN PROGRESS - Synergy metric development started
- **Phase 3-5**: PENDING
