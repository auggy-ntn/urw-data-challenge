# URW x HEC Data Challenge - Project Roadmap

## Project Goal

**Design a data-driven framework to assess, simulate, and recommend optimal retail mixes** that maximize the overall value of URW shopping centers in terms of revenue, visitor engagement, efficiency, and future-readiness.

The primary deliverable is a **robust analytical approach** with clear justification, not just raw results.

### Key Business Questions

1. What is the "ideal" tenant composition for a given mall profile?
2. How does adding, removing, or relocating a tenant impact others and the mall as a whole?
3. How can URW proactively adapt the retail mix to emerging trends?

---

## KPIs and Metrics Framework

### Mall-Level Performance Metrics

| Metric | Description | Data Source |
|--------|-------------|-------------|
| **Total Footfall** | Daily/monthly visitor count | `fact_malls_v1.people_in` |
| **Dwell Time** | Average time spent in mall | `fact_malls_v1.average_dwell_time` |
| **Sales Density** | Total sales / Total GLA | `store_financials_v1`, `dim_blocks_v1` |
| **Occupancy Rate** | Leased GLA / Total GLA | `dim_blocks_v1` |

### Store-Level Performance Metrics

| Metric | Description | Data Source |
|--------|-------------|-------------|
| **Capture Rate** | `people_in / people_window_flow` | `fact_stores_v1` |
| **Sales per sqm** | `sales_r12m / gla` | `store_financials_v1`, `dim_blocks_v1` |
| **Occupancy Cost Ratio (OCR)** | `total_costs_r12m / sales_r12m` | `store_financials_v1` |
| **Store Dwell Time** | Time spent inside store | `fact_stores_v1.store_average_dwell_time` |
| **Cross-Visit Index** | Avg co-visits with other stores | `cross_visits_v1` |
| **Sustainability Score** | SRI rating | `fact_sri_scores_v1.sri_score` |

### Retail Mix Quality Metrics

| Metric | Description | Purpose |
|--------|-------------|---------|
| **Category Diversity Index** | Shannon entropy of BL1/BL2 categories | Measure tenant variety |
| **Anchor-Satellite Ratio** | Large stores vs small/medium | Balance of traffic drivers |
| **Synergy Score** | Aggregate cross-visit strength | Measure tenant complementarity |
| **Sustainability Mix Score** | Weighted avg SRI of tenant base | ESG readiness |

---

## Phase 1: Data Foundation & Exploration

### 1.1 Data Ingestion & Quality Assessment
- Load all datasets and verify schema against data dictionary
- Profile data: missing values, outliers, distributions
- Validate joins between tables (store_code, mall_id)
- Document data quality issues and coverage gaps

### 1.2 Exploratory Data Analysis (EDA)
- **Mall profiles**: Compare Vélizy 2, Parly 2, Euralille on size, footfall, category mix
- **Temporal patterns**: Day-of-week, seasonality in footfall and sales
- **Category analysis**: Performance by BL1/BL2/BL3 categories
- **Store size analysis**: Performance differences by GLA category
- **Financial health**: Distribution of OCR, identify over/under-performers

### Deliverables
- Data quality report
- EDA notebook with visualizations
- Initial insights presentation

---

## Phase 2: Store Performance Modeling

### 2.1 Store Performance Scoring
Build a composite performance score combining:
- Sales efficiency (sales per sqm)
- Traffic conversion (capture rate)
- Engagement (dwell time)
- Financial health (inverse of OCR)
- Sustainability (SRI score)

### 2.2 Performance Drivers Analysis
- Regression models: What factors predict store performance?
  - Location (floor, zone, proximity to anchors)
  - Category
  - Store size
  - Neighboring stores
- Identify underperforming stores relative to their category benchmarks

### Deliverables
- Store performance scoring methodology
- Feature importance analysis
- Underperformer identification framework

---

## Phase 3: Tenant Synergy Analysis

### 3.1 Cross-Visit Network Analysis
- Build store co-visitation graph from `cross_visits_v1`
- Compute network metrics:
  - Degree centrality (traffic hubs)
  - Betweenness centrality (bridge stores)
  - Community detection (natural store clusters)
- Identify high-synergy store pairs/groups

### 3.2 Category Affinity Matrix
- Aggregate cross-visits by BL2/BL3 categories
- Build category affinity heatmap
- Identify complementary vs. competing categories
- Quantify cannibalization risk between similar retailers

### 3.3 Anchor Effect Analysis
- Measure traffic spillover from large stores (anchors)
- Quantify the "halo effect" on nearby smaller stores
- Model anchor removal scenarios

### Deliverables
- Synergy network visualization
- Category affinity matrix
- Anchor impact quantification

---

## Phase 4: Retail Mix Optimization Framework

### 4.1 Define Optimization Objectives
Multi-objective optimization balancing:
1. **Revenue maximization**: Total mall sales
2. **Traffic optimization**: Footfall and dwell time
3. **Tenant health**: Minimize OCR across tenants
4. **Diversity**: Maintain category balance
5. **Sustainability**: Improve average SRI score

### 4.2 Constraint Definition
- Total GLA constraint per mall
- Minimum/maximum stores per category (avoid over-concentration)
- Anchor store requirements
- Sustainability targets

### 4.3 Simulation Engine
Build a simulator to answer "what-if" questions:
- **Tenant addition**: Predict impact of adding a new category/retailer
- **Tenant removal**: Estimate traffic/sales loss and redistribution
- **Tenant relocation**: Model proximity effects
- **Category rebalancing**: Simulate shift from one category to another

### 4.4 Recommendation Engine
- Given a mall profile, recommend:
  - Optimal category mix (% GLA per BL1/BL2)
  - High-potential tenant additions
  - Underperformers to consider replacing
  - Relocation opportunities for synergy gains

### Deliverables
- Optimization model specification
- Simulation engine (Python module)
- Recommendation logic with explainability

---

## Phase 5: Visualization & Delivery

### 5.1 Streamlit Dashboard (Bonus)
Interactive application with:
- **Mall Overview**: KPIs, category breakdown, sustainability score
- **Store Explorer**: Performance metrics, cross-visit network
- **What-If Simulator**: Add/remove/relocate tenants
- **Recommendations Panel**: Suggested optimizations with rationale

### 5.2 Final Presentation
- Executive summary of methodology
- Key insights from the data
- Framework demonstration
- Strategic recommendations for URW
- Limitations and future directions

### Deliverables
- Streamlit app
- Presentation deck
- Technical documentation

---

## Suggested Timeline (2 Weeks)

| Days | Phase | Focus |
|------|-------|-------|
| 1-2 | Phase 1 | Data loading, quality checks, initial EDA |
| 3-4 | Phase 1-2 | Complete EDA, begin performance modeling |
| 5-6 | Phase 2-3 | Performance scoring, network analysis |
| 7-8 | Phase 3 | Synergy analysis, category affinity |
| 9-10 | Phase 4 | Optimization framework, simulation engine |
| 11-12 | Phase 4-5 | Recommendations, Streamlit dashboard |
| 13-14 | Phase 5 | Polish deliverables, prepare presentation |

---

## Technical Approach Options

The brief explicitly encourages combining multiple techniques:

### Machine Learning
- Regression for performance prediction
- Clustering for store/mall segmentation
- Time series for trend forecasting

### Network Analysis
- Graph-based synergy modeling
- Community detection for natural store groupings
- Centrality measures for anchor identification

### Optimization
- Linear/Mixed Integer Programming for GLA allocation
- Multi-objective optimization for balancing KPIs
- Constraint satisfaction for feasibility

### Simulation
- Monte Carlo for uncertainty quantification
- Agent-based modeling for visitor flow
- Scenario analysis for strategic planning

### Generative AI (Optional)
- LLM-assisted trend analysis from external data
- Natural language recommendations

---

## Sustainability Integration (Bonus)

Incorporate sustainability throughout:

1. **Current State Assessment**
   - Analyze SRI score distribution across malls
   - Identify sustainability leaders/laggards by category

2. **Sustainability-Aware Optimization**
   - Add SRI improvement as an objective
   - Penalize low-SRI tenant additions
   - Model sustainability improvement trajectories

3. **Reporting**
   - Sustainability dashboard panel
   - ESG-aligned recommendations

---

## Risk Factors & Mitigations

| Risk | Mitigation |
|------|------------|
| Incomplete financial data | Use available stores as benchmarks; impute by category |
| Cross-visit data sparsity | Aggregate to category level for robust patterns |
| Limited mall sample (3 malls) | Focus on transferable methodology over mall-specific results |
| Short timeframe | Prioritize framework design over polish |

---

## Success Criteria

The solution will be evaluated on:

1. **Analytical Rigor**: Sound methodology with clear justification
2. **Business Relevance**: Actionable insights for URW decision-makers
3. **Innovation**: Creative use of available data and techniques
4. **Presentation**: Clear communication of approach and findings
5. **Bonus**: Streamlit interface and sustainability integration

---

## Next Steps

1. Pull data with `dvc pull`
2. Create initial EDA notebook
3. Begin Phase 1 data profiling
