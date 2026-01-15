"""Functions for the swap predictor engine.

The swap predictor estimates performance changes when swapping a store by a store from
another category.
It does this by using the store performance predictor model to estimate the new store's
performance in the target location. It also estimates the impact on neighboring stores
based on category affinities.
"""

import pandas as pd

from src.utils import columns as col
from src.utils.train_model import engineer_store_features


def compute_synergy_score(
    store_category: str,
    neighbor_categories: pd.Series,
    affinity_matrix: pd.DataFrame,
) -> float:
    """Compute synergy score for a store given its neighbors' categories.

    Args:
        store_category: The category of the store.
        neighbor_categories: Series with category counts of neighboring stores.
        affinity_matrix: Affinity matrix for categories.

    Returns:
        Synergy score (sum of affinity × neighbor_count for each neighbor category).
    """
    synergy_score = 0.0
    for neighbor_cat, count in neighbor_categories.items():
        affinity_row = affinity_matrix.loc[
            (affinity_matrix[col.CATEGORY_A] == store_category)
            & (affinity_matrix[col.CATEGORY_B] == neighbor_cat)
        ]
        if len(affinity_row) > 0:
            affinity_val = affinity_row[col.AFFINITY].values[0]
            if pd.notna(affinity_val):
                synergy_score += affinity_val * count
    return synergy_score


def get_store_neighbors(store_code: int, cross_visits: pd.DataFrame) -> set:
    """Get all neighbor store codes for a given store."""
    store_cross = cross_visits[
        (cross_visits[col.STORE_CODE_1] == store_code)
        | (cross_visits[col.STORE_CODE_2] == store_code)
    ]
    neighbor_codes = set(store_cross[col.STORE_CODE_1]) | set(
        store_cross[col.STORE_CODE_2]
    )
    neighbor_codes.discard(store_code)
    return neighbor_codes


def encode_features_for_prediction(
    features: dict,
    encoders: dict,
) -> pd.DataFrame:
    """Encode a single store's features for model prediction.

    Args:
        features: Dictionary of features for a store.
        encoders: Dictionary of LabelEncoders for categorical columns.

    Returns:
        DataFrame with encoded features ready for prediction.
    """
    features_df = pd.DataFrame([features])
    for column, encoder in encoders.items():
        if column in features_df.columns:
            val = str(features_df[column].iloc[0])
            if val in encoder.classes_:
                features_df[column] = encoder.transform([val])[0]
            else:
                features_df[column] = 0
    return features_df


def compute_gla_weighted_sri(
    store_sri: pd.Series,
    store_gla: pd.Series,
) -> float:
    """Compute GLA-weighted average SRI score.

    Args:
        store_sri: Series with SRI scores indexed by store_code.
        store_gla: Series with GLA indexed by store_code.

    Returns:
        GLA-weighted average SRI (larger stores contribute more).
    """
    # Align indices - only include stores that have both SRI and GLA
    common_stores = store_sri.index.intersection(store_gla.index)
    sri_aligned = store_sri.loc[common_stores]
    gla_aligned = store_gla.loc[common_stores]

    # Drop NaN values
    valid_mask = sri_aligned.notna() & gla_aligned.notna()
    sri_valid = sri_aligned[valid_mask]
    gla_valid = gla_aligned[valid_mask]

    if gla_valid.sum() == 0:
        return sri_valid.mean() if len(sri_valid) > 0 else 0.0

    return (sri_valid * gla_valid).sum() / gla_valid.sum()


def compute_mall_composite_score(
    avg_sales: float,
    avg_dwell: float,
    avg_sri: float,
    weights: dict = None,
) -> float:
    """Compute weighted composite mall score.

    Args:
        avg_sales: Average sales per sqm (normalized, 1.0 = baseline).
        avg_dwell: Average dwell time (normalized, 1.0 = baseline).
        avg_sri: Average SRI score (raw score, typically 10-50).
        weights: Dictionary with weights for each metric. Default: equal weights.

    Returns:
        Composite score (higher is better).
    """
    if weights is None:
        weights = {"sales": 0.4, "dwell": 0.3, "sri": 0.3}

    # Normalize SRI to similar scale (assuming typical range 10-50, normalize to ~1.0)
    sri_normalized = avg_sri / 30.0  # 30 as a reasonable midpoint

    score = (
        weights["sales"] * avg_sales
        + weights["dwell"] * avg_dwell
        + weights["sri"] * sri_normalized
    )
    return score


def predict_swap_impact(
    store_to_swap: int,
    new_category: str,
    models: dict,
    encoders: dict,
    dim_blocks: pd.DataFrame,
    store_total: pd.DataFrame,
    cross_visits: pd.DataFrame,
    affinity_matrix: pd.DataFrame,
    current_store_performance: pd.DataFrame,
    current_store_sri: pd.DataFrame,
    category_sri_avg: pd.Series,
    weights: dict = None,
) -> dict:
    """Predict the impact of swapping a store to a new category.

    Computes mall-level composite score using:
    - Average sales per sqm
    - Average dwell time
    - GLA-weighted average SRI score (larger stores have more impact)

    Args:
        store_to_swap: Store code of the store to swap.
        new_category: The new bl1_label category to swap to.
        models: Dict with trained models for 'sales_per_sqm' and 'dwell_time'.
        encoders: Dictionary of LabelEncoders for categorical features.
        dim_blocks: Dimension table for blocks.
        store_total: Aggregated store data.
        cross_visits: Cross visits data.
        affinity_matrix: Affinity matrix for categories.
        current_store_performance: DataFrame with current relative performance.
        current_store_sri: Series with SRI scores indexed by store_code.
        category_sri_avg: pd.Series mapping category to average SRI.
        weights: Dict with weights for composite score (sales, dwell, sri).

    Returns:
        Dictionary with current and predicted mall metrics and composite scores.
    """
    # Get store info
    store_info = dim_blocks[dim_blocks[col.STORE_CODE] == store_to_swap].iloc[0]
    mall_id = store_info[col.MALL_ID]
    old_category = store_info[col.CAT_HIGH]
    store_gla = store_info[col.GLA]

    # Get all stores in the mall with their GLA
    mall_stores = dim_blocks[dim_blocks[col.MALL_ID] == mall_id].drop_duplicates(
        subset=[col.STORE_CODE]
    )
    mall_store_codes = set(mall_stores[col.STORE_CODE])
    mall_store_gla = mall_stores.set_index(col.STORE_CODE)[col.GLA]

    # Get neighbors of the store to swap
    neighbors = get_store_neighbors(store_to_swap, cross_visits)

    ##### Build new store features after swap #####
    new_store_features = engineer_store_features(
        store_to_swap, dim_blocks, store_total, cross_visits, affinity_matrix
    )
    new_store_features[col.MODEL_STORE_CATEGORY] = new_category

    # Recalculate synergy with new category
    neighbor_categories = dim_blocks[dim_blocks[col.STORE_CODE].isin(neighbors)][
        col.CAT_HIGH
    ].value_counts()
    new_store_features[col.MODEL_STORE_NEIGHBORHOOD_SYNERGY] = compute_synergy_score(
        new_category, neighbor_categories, affinity_matrix
    )

    # Recalculate category share in mall
    current_new_cat_gla = mall_stores[mall_stores[col.CAT_HIGH] == new_category][
        col.GLA
    ].sum()
    mall_total_gla = new_store_features[col.MODEL_MALL_TOTAL_GLA]
    new_store_features[col.MODEL_MALL_CATEGORY_SHARE] = (
        current_new_cat_gla + store_gla
    ) / mall_total_gla

    ##### Predict new store performance #####
    new_store_encoded = encode_features_for_prediction(new_store_features, encoders)

    pred_sales = models["sales_per_sqm"].predict(new_store_encoded)[0]
    pred_dwell = models["dwell_time"].predict(new_store_encoded)[0]
    pred_sri = category_sri_avg.get(
        new_category, 0.0
    )  # Default to 0 if category not found

    ##### Compute current mall metrics #####
    mall_perf = current_store_performance.loc[
        current_store_performance.index.isin(mall_store_codes)
    ]
    mall_sri = current_store_sri.loc[current_store_sri.index.isin(mall_store_codes)]

    current_avg_sales = mall_perf[col.TARGET_SALES_PER_SQM].mean()
    current_avg_dwell = mall_perf[col.TARGET_DWELL_TIME].mean()
    # GLA-weighted SRI
    current_avg_sri = compute_gla_weighted_sri(mall_sri, mall_store_gla)

    ##### Compute new mall metrics (after swap) #####
    # Update sales
    new_mall_sales = mall_perf[col.TARGET_SALES_PER_SQM].copy()
    new_mall_sales.loc[store_to_swap] = pred_sales
    new_avg_sales = new_mall_sales.mean()

    # Update dwell
    new_mall_dwell = mall_perf[col.TARGET_DWELL_TIME].copy()
    new_mall_dwell.loc[store_to_swap] = pred_dwell
    new_avg_dwell = new_mall_dwell.mean()

    # Update SRI (use category average for new store) - GLA-weighted
    new_mall_sri = mall_sri.copy()
    if store_to_swap in new_mall_sri.index:
        new_mall_sri.loc[store_to_swap] = pred_sri
    else:
        new_mall_sri = pd.concat(
            [new_mall_sri, pd.Series([pred_sri], index=[store_to_swap])]
        )
    new_avg_sri = compute_gla_weighted_sri(new_mall_sri, mall_store_gla)

    ##### Compute composite scores #####
    current_composite = compute_mall_composite_score(
        current_avg_sales, current_avg_dwell, current_avg_sri, weights
    )
    new_composite = compute_mall_composite_score(
        new_avg_sales, new_avg_dwell, new_avg_sri, weights
    )

    composite_improvement = (
        (new_composite - current_composite) / current_composite
    ) * 100

    ### Prepare result dictionary #####
    result = {
        "swapped_store": {
            "store_code": store_to_swap,
            "old_category": old_category,
            "new_category": new_category,
            "gla": store_gla,
            "gla_share": store_gla / mall_total_gla,
        },
        "current_mall_metrics": {
            "mall_id": mall_id,
            "avg_sales_per_sqm": current_avg_sales,
            "avg_dwell_time": current_avg_dwell,
            "avg_sri_gla_weighted": current_avg_sri,
            "composite_score": current_composite,
        },
        "predicted_mall_metrics": {
            "mall_id": mall_id,
            "avg_sales_per_sqm": new_avg_sales,
            "avg_dwell_time": new_avg_dwell,
            "avg_sri_gla_weighted": new_avg_sri,
            "composite_score": new_composite,
        },
        "improvement": {
            "sales_pct": ((new_avg_sales - current_avg_sales) / current_avg_sales)
            * 100,
            "dwell_pct": ((new_avg_dwell - current_avg_dwell) / current_avg_dwell)
            * 100,
            "sri_pct": ((new_avg_sri - current_avg_sri) / current_avg_sri) * 100,
            "composite_pct": composite_improvement,
        },
        "new_store_predictions": {
            "sales_per_sqm": pred_sales,
            "dwell_time": pred_dwell,
            "sri": pred_sri,
        },
    }

    return result
