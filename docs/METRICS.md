# Metrics Reference

This document describes the metrics used in the URW Data Challenge project, their computation methods, and business interpretation in the context of shopping mall tenant mix optimization.

---

## Overview

Metrics are organized into three levels:

1. **Store-level metrics**: Individual store performance and synergy position
2. **Mall-level metrics**: Aggregated performance and tenant mix quality
3. **Composite score**: Weighted combination for optimization objective

---

## Synergy Metrics (Graph-Based)

Synergy metrics quantify how well stores complement each other based on cross-visitation patterns. A store graph is constructed where:
- **Nodes** = Stores (or retailers/categories depending on granularity)
- **Edges** = Cross-visits between stores
- **Edge weight** = `total_cross_visits` (number of shared visitors)

### Store-Level Synergy Metrics (Node Metrics)

These metrics characterize each store's position in the co-visitation network.

| Metric | Computation | Business Meaning |
|--------|-------------|------------------|
| **Degree** | Number of connected stores | How many other stores share visitors with this one |
| **Weighted Degree (Strength)** | Sum of edge weights | Total cross-visit volume; measures overall synergy contribution |
| **Degree Centrality** | Degree / (n_nodes - 1) | Normalized connectivity; identifies hub stores |
| **Betweenness Centrality** | Fraction of shortest paths passing through node | Bridge stores that connect otherwise separate clusters; critical for mall flow |
| **PageRank** | Iterative importance score | Stores that receive traffic from other important stores; captures "quality" of connections |
| **Clustering Coefficient** | Fraction of neighbor pairs that are connected | Whether the store is part of a tight-knit shopping cluster |
| **Eigenvector Centrality** | Weighted sum of neighbor centralities | Being connected to well-connected stores; influence in the network |

#### Business Interpretation

- **High weighted degree**: Anchor stores that drive traffic to many others (e.g., hypermarkets, popular fashion retailers)
- **High betweenness**: Stores positioned at the intersection of shopping journeys; removing them may fragment the mall experience
- **High clustering**: Stores in cohesive groups (e.g., food court cluster, luxury cluster); indicates natural shopping zones
- **High PageRank**: Stores that benefit from being near important neighbors; good location value

### Mall-Level Synergy Metrics (Graph Metrics)

These metrics characterize the overall synergy quality of the tenant mix.

| Metric | Computation | Business Meaning |
|--------|-------------|------------------|
| **Density** | Actual edges / possible edges | Completeness of cross-visitation; high density = visitors explore more of the mall |
| **Avg Weighted Degree** | Mean of node weighted degrees | Overall synergy level; higher = more cross-shopping |
| **Std Weighted Degree** | Std dev of weighted degrees | Dispersion of synergy; high std = uneven distribution |
| **Gini Weighted Degree** | Gini coefficient of weighted degrees | Concentration measure (0 = equal distribution, 1 = all synergy in one store) |
| **Top-5 Degree Share** | Sum of top 5 weighted degrees / total | Anchor dominance; how much synergy is driven by top stores |
| **Avg Clustering** | Mean of node clustering coefficients | Overall clustering tendency; high = strong local shopping clusters |
| **Transitivity** | Global clustering coefficient | Probability that adjacent nodes of a node are connected |
| **Degree Assortativity** | Correlation of degrees at edge endpoints | Do hubs connect to hubs? Positive = yes, negative = hubs connect to periphery |
| **Modularity** | Quality of community partition (Louvain) | How well the network divides into distinct communities; high modularity = siloed tenant groups |
| **N Communities** | Number of detected communities | Natural shopping clusters in the mall |
| **N Connected Components** | Number of disconnected subgraphs | Should be 1 for a healthy mall; >1 indicates isolated store groups |
| **Avg Path Length** | Mean shortest path between all node pairs | How "close" stores are in terms of visitor flow; lower = easier navigation |

#### Business Interpretation

- **High density + low modularity**: Well-integrated mall where visitors flow freely between all areas
- **High modularity**: Distinct shopping zones; may indicate good category clustering OR problematic silos
- **Low Gini coefficient**: Synergy is distributed across many stores; less dependent on anchors
- **High top-5 share**: Mall heavily dependent on a few anchor stores for cross-traffic
- **Positive assortativity**: Hub stores cluster together; may create "hot zones" and "dead zones"

#### Recommended Metrics for Composite Score

For predicting mall performance, prioritize:

1. **Density** - Direct measure of cross-visitation completeness
2. **Avg Weighted Degree** - Overall synergy level
3. **Gini Weighted Degree** - Distribution of synergy (penalize concentration)
4. **Modularity** - Quality of natural tenant clusters

---

## Store-Level Performance Metrics

*To be documented as implemented.*

| Metric | Description | Data Source |
|--------|-------------|-------------|
| Capture Rate | `people_in / people_window_flow` | `fact_stores_v1` |
| Sales per sqm | `sales_r12m / gla` | `store_financials_v1`, `dim_blocks_v1` |
| OCR | `total_costs_r12m / sales_r12m` | `store_financials_v1` |
| Store Dwell Time | Average time in store | `fact_stores_v1` |
| SRI Score | Sustainability rating | `fact_sri_scores_v1` |

---

## Mall-Level Performance Metrics

*To be documented as implemented.*

### Direct Metrics

| Metric | Description | Data Source |
|--------|-------------|-------------|
| Total Footfall | Daily/monthly visitor count | `fact_malls_v1.people_in` |
| Mall Dwell Time | Average time in mall | `fact_malls_v1.average_dwell_time` |
| Occupancy Rate | Leased GLA / Total GLA | `dim_blocks_v1` |

### Aggregated from Store Metrics

| Metric | Aggregation | Source |
|--------|-------------|--------|
| Avg Sales Density | Mean of store sales/sqm | Sales per sqm |
| Avg OCR | Mean or GLA-weighted | OCR |
| % Healthy Tenants | % stores with OCR < threshold | OCR |
| Avg SRI Score | Mean or GLA-weighted | SRI score |

### Tenant Mix Quality

| Metric | Description |
|--------|-------------|
| Category Diversity Index | Shannon entropy of BL1/BL2 categories |
| Anchor-Satellite Ratio | Large stores vs small/medium |
| Synergy Score | Aggregate from graph metrics above |

---

## Composite Score

*To be defined in Phase 3.*

The optimization objective combines multiple components:

```
Composite Score = w1 * Revenue Component
                + w2 * Traffic Component
                + w3 * Tenant Health Component
                + w4 * Synergy Component
                + w5 * Sustainability Component
                + w6 * Diversity Component
```

Weights (w1-w6) will be tuned based on URW's strategic priorities.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-11 | Initial version with synergy metrics documentation |
