"""Model training utilities and pipelines."""

import joblib
import pandas as pd

# TODO: Add option to use other models
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, LeaveOneGroupOut, cross_val_score
from sklearn.preprocessing import LabelEncoder

from constants import column_names as col
from constants import paths as pth
from src.utils.logger import logger


def save_model_artifacts(
    models: dict,
    encoders: dict,
    mall_means: dict,
) -> None:
    """Save trained models and related artifacts to disk.

    Args:
        models: Dictionary mapping target names to trained models.
        encoders: Dictionary mapping target names to their label encoders.
        mall_means: Dictionary mapping target names to mall mean values.
    """
    # Create models directory if it doesn't exist
    pth.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Save individual model files
    for target_name, model in models.items():
        model_path = pth.MODELS_DIR / f"{target_name}_model.joblib"
        logger.info(f"Saving {target_name} model to {model_path}")
        joblib.dump(model, model_path)

    # Save individual encoder files
    for target_name, target_encoders in encoders.items():
        encoder_path = pth.MODELS_DIR / f"{target_name}_encoders.joblib"
        logger.info(f"Saving {target_name} encoders to {encoder_path}")
        joblib.dump(target_encoders, encoder_path)

    # Save mall means as CSV
    mall_means_rows = []
    for target_name, mall_dict in mall_means.items():
        for mall_id, mean_value in mall_dict.items():
            mall_means_rows.append(
                {
                    "target": target_name,
                    "mall_id": mall_id,
                    "mean_value": mean_value,
                }
            )
    mall_means_df = pd.DataFrame(mall_means_rows)
    logger.info(f"Saving mall means to {pth.MALL_MEANS}")
    mall_means_df.to_csv(pth.MALL_MEANS, index=False)

    logger.info("All model artifacts saved successfully.")


def engineer_store_features(
    store_code: int,
    dim_blocks: pd.DataFrame,
    store_total: pd.DataFrame,
    cross_visits: pd.DataFrame,
    affinity_matrix: pd.DataFrame,
) -> pd.DataFrame:
    """Engineer features for a given store.

    Args:
        store_code (int): The store code.
        dim_blocks (pd.DataFrame): Dimension table for blocks.
        store_total (pd.DataFrame): Aggregated store data over the entire period.
        cross_visits (pd.DataFrame): Cross visits data between stores.
        affinity_matrix (pd.DataFrame): Affinity matrix for categories.

    Returns:
        dict: A dictionary of engineered features for the store.
    """
    features = {}

    # There are duplicate store codes in dim_blocks, correspond to stores that span over
    # multiple blocks. The gla corresponds to the sum of the gla of all blocks, so we
    # can take any of the rows for other store attributes.
    store_info = dim_blocks[dim_blocks[col.STORE_CODE] == store_code].iloc[0]
    mall_id = store_info[col.MALL_ID]
    store_category = store_info[col.CAT_HIGH]

    # Get neighboring stores based on cross visits
    store_cross = cross_visits[
        (cross_visits[col.STORE_CODE_1] == store_code)
        | (cross_visits[col.STORE_CODE_2] == store_code)
    ]

    neighbor_codes = set(store_cross[col.STORE_CODE_1]) | set(
        store_cross[col.STORE_CODE_2]
    )
    neighbor_codes.discard(store_code)

    # Get category distribution of neighboring stores
    neighbor_categories = dim_blocks[dim_blocks[col.STORE_CODE].isin(neighbor_codes)][
        col.CAT_HIGH
    ].value_counts()

    # Compute synergy score: sum of (affinity × neighbor_count) for each neighbor
    # category
    synergy_score = 0
    for neighbor_cat, count in neighbor_categories.items():
        affinity_score = affinity_matrix.loc[
            (affinity_matrix[col.CATEGORY_A] == store_category)
            & (affinity_matrix[col.CATEGORY_B] == neighbor_cat)
        ][col.AFFINITY].values
        if len(affinity_score) > 0 and pd.notna(affinity_score[0]):
            synergy_score += affinity_score[0] * count

    mall_stores = dim_blocks[dim_blocks[col.MALL_ID] == mall_id].drop_duplicates(
        subset=[col.STORE_CODE]
    )

    #### Features ####
    # Mall ID (categorical)
    features[col.MALL_ID] = mall_id

    # Intrinsic store features
    features[col.MODEL_STORE_GLA] = store_info[col.GLA]
    features[col.MODEL_STORE_GLA_CAT] = store_info[col.GLA_CAT]
    features[col.MODEL_STORE_CATEGORY] = store_category

    # Location features
    features[col.MODEL_STORE_AVG_WINDOW_FLOW] = store_total.loc[
        store_code, col.MODEL_STORE_AVG_WINDOW_FLOW
    ]
    features[col.MODEL_STORE_MEDIAN_WINDOW_FLOW] = store_total.loc[
        store_code, col.MODEL_STORE_MEDIAN_WINDOW_FLOW
    ]

    # Neighborhood synergy feature
    features[col.MODEL_STORE_NEIGHBORHOOD_SYNERGY] = synergy_score
    features[col.MODEL_STORE_NB_NEIGHBORS] = len(neighbor_codes)

    # Mall features
    features[col.MODEL_MALL_TOTAL_GLA] = mall_stores[col.GLA].sum()
    features[col.MODEL_MALL_STORE_COUNT] = len(mall_stores)
    features[col.MODEL_MALL_CATEGORY_SHARE] = (
        mall_stores[mall_stores[col.CAT_HIGH] == store_category][col.GLA].sum()
        / features[col.MODEL_MALL_TOTAL_GLA]
    )

    return features


def build_training_dateset(
    dim_blocks: pd.DataFrame,
    store_total: pd.DataFrame,
    cross_visits: pd.DataFrame,
    affinity_matrix: pd.DataFrame,
    store_financials: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, dict, list]:
    """Build the training dataset by engineering features for all stores.

    Args:
        dim_blocks (pd.DataFrame): Dimension table for blocks.
        store_total (pd.DataFrame): Aggregated store data.
        cross_visits (pd.DataFrame): Cross visits data between stores.
        affinity_matrix (pd.DataFrame): Affinity matrix for categories.
        store_financials (pd.DataFrame): Store financials data (for target variable).

    Returns:
        pd.DataFrame: The training dataset with engineered features for all stores.
        pd.DataFrame: The target variables (normalized by mall mean).
        pd.Series: Mall IDs for each store (for leave-one-mall-out CV).
        dict: Mall means for each target (to convert predictions back to absolute).
        list: Store codes in the same order as features/targets (for index alignment).
    """
    # There are some stores in store_total that are not in dim_blocks, which we skip
    # as we cannot engineer features for them (like category, mall, etc.)
    valid_store_codes = set(dim_blocks[col.STORE_CODE]) & set(store_total.index)
    store_total = store_total.loc[list(valid_store_codes)]

    # Merge financials and GLA
    store_total_merged = pd.merge(
        store_total,
        store_financials,
        on=col.STORE_CODE,
        how="left",
        validate="1:1",
    )

    store_total_merged = pd.merge(
        store_total_merged,
        dim_blocks[[col.STORE_CODE, col.GLA]].drop_duplicates(subset=[col.STORE_CODE]),
        on=col.STORE_CODE,
        how="left",
        validate="1:1",
    )

    store_total_merged = store_total_merged.set_index(col.STORE_CODE)

    # Engineer features for all stores
    feature_list = []
    store_codes_order = []  # Track the order of stores
    for store_code in store_total.index:
        features = engineer_store_features(
            store_code,
            dim_blocks,
            store_total,
            cross_visits,
            affinity_matrix,
        )
        feature_list.append(pd.Series(features, name=store_code))
        store_codes_order.append(store_code)

    features_df = pd.DataFrame(feature_list)
    features_df.index.name = col.STORE_CODE

    # Compute raw targets aligned with features index
    targets_raw = pd.DataFrame(index=features_df.index)
    targets_raw[col.TARGET_CAPTURE_RATE] = (
        store_total_merged.loc[features_df.index, col.MODEL_STORE_TOTAL_PEOPLE_IN]
        / store_total_merged.loc[features_df.index, col.MODEL_STORE_TOTAL_WINDOW_FLOW]
    )
    targets_raw[col.TARGET_SALES_PER_SQM] = (
        store_total_merged.loc[features_df.index, col.SALES_R12M]
        / store_total_merged.loc[features_df.index, col.GLA]
    )
    targets_raw[col.TARGET_DWELL_TIME] = store_total_merged.loc[
        features_df.index, col.MODEL_STORE_AVG_DWELL_TIME
    ]

    # Replace inf values with NaN to avoid polluting mall means
    import numpy as np

    targets_raw = targets_raw.replace([np.inf, -np.inf], np.nan)

    # Get mall_ids for normalization and CV
    store_to_mall = dim_blocks.drop_duplicates(subset=[col.STORE_CODE]).set_index(
        col.STORE_CODE
    )[col.MALL_ID]
    mall_ids = store_to_mall.loc[features_df.index]

    # Compute mall means for each target (excluding inf/nan values)
    targets_raw[col.MALL_ID] = mall_ids.values
    mall_means = {}
    for target_col in [
        col.TARGET_CAPTURE_RATE,
        col.TARGET_SALES_PER_SQM,
        col.TARGET_DWELL_TIME,
    ]:
        # Use only finite values for computing mall means
        mall_means[target_col] = (
            targets_raw.groupby(col.MALL_ID)[target_col].mean().to_dict()
        )

    # Normalize targets by mall mean (1.0 = mall average)
    targets = pd.DataFrame(index=features_df.index)
    for target_col in [
        col.TARGET_CAPTURE_RATE,
        col.TARGET_SALES_PER_SQM,
        col.TARGET_DWELL_TIME,
    ]:
        mall_mean_series = mall_ids.map(mall_means[target_col])
        targets[target_col] = targets_raw[target_col] / mall_mean_series

    # Reset indexes for alignment
    mall_ids = mall_ids.reset_index(drop=True)
    features_df = features_df.reset_index(drop=True)
    targets = targets.reset_index(drop=True)

    return features_df, targets, mall_ids, mall_means, store_codes_order


def train_performance_model(X, y, target_col, mall_ids, cv_strategy="kfold"):
    """Train a performance prediction model.

    Args:
        X: Feature DataFrame
        y: Target DataFrame (normalized by mall mean, so 1.0 = average)
        target_col: Which target to predict
        mall_ids: Series with mall_id for each row (aligned with X and y)
        cv_strategy: "kfold" (default) or "leave_mall_out"

    Returns:
        Trained model, encoders, CV scores
    """
    # Mask rows where target is NaN
    mask_target = y[target_col].notna()
    X_filtered = X.loc[mask_target].copy()
    y_filtered = y.loc[mask_target]
    groups = mall_ids.loc[mask_target]

    # Encode categorical features
    cat_cols = X_filtered.select_dtypes(include=["object"]).columns.tolist()
    # mall_id is int, need to add it to categorical encoding
    if col.MALL_ID in X_filtered.columns:
        cat_cols.append(col.MALL_ID)

    encoders = {}
    for column in cat_cols:
        le = LabelEncoder()
        X_filtered[column] = le.fit_transform(X_filtered[column].astype(str))
        encoders[column] = le

    # Prepare target
    y_target = y_filtered[target_col]

    # Model
    model = RandomForestRegressor(
        n_estimators=1000, max_depth=10, min_samples_leaf=5, random_state=42, n_jobs=-1
    )

    # Cross-validation
    if cv_strategy == "kfold":
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, X_filtered, y_target, cv=cv, scoring="r2")
    else:
        # Leave-one-mall-out (note: mall_id feature won't generalize to unseen malls)
        logo = LeaveOneGroupOut()
        cv_scores = cross_val_score(
            model, X_filtered, y_target, cv=logo, groups=groups, scoring="r2"
        )

    logger.info(f"Target: {target_col}")
    logger.info(f"CV strategy: {cv_strategy}")
    logger.info(f"CV R² scores: {cv_scores}")
    logger.info(f"Mean R²: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    # Fit final model on all data
    model.fit(X_filtered, y_target)

    return model, encoders, cv_scores


def training_pipeline():
    """Full training pipeline to load data, engineer features, and train models."""
    logger.info("Starting model training pipeline...")

    # Load the data
    try:
        logger.info(f"Loading enriched store metrics from {pth.ENRICHED_STORE_METRICS}")
        store_metrics = pd.read_csv(
            pth.ENRICHED_STORE_METRICS, index_col=col.STORE_CODE
        )

        logger.info(f"Loading dimension blocks from {pth.INTERMEDIATE_DIM_BLOCKS}")
        dim_blocks = pd.read_csv(pth.INTERMEDIATE_DIM_BLOCKS)

        logger.info(f"Loading cross visits from {pth.INTERMEDIATE_CROSS_VISITS}")
        cross_visits = pd.read_csv(pth.INTERMEDIATE_CROSS_VISITS)

        logger.info(f"Loading affinity matrix from {pth.ENRICHED_CATEGORY_AFFINITIES}")
        affinity_matrix = pd.read_csv(pth.ENRICHED_CATEGORY_AFFINITIES)

        logger.info(
            f"Loading store financials from {pth.INTERMEDIATE_STORE_FINANCIALS}"
        )
        store_financials = pd.read_csv(pth.INTERMEDIATE_STORE_FINANCIALS)

    except Exception as e:
        logger.error(f"Error loading data: {e}, try running data pipelines first.")
        raise e

    # Build training dataset
    logger.info("Building training dataset with engineered features...")
    X, y, mall_ids, mall_means, store_codes_order = build_training_dateset(
        dim_blocks,
        store_metrics,
        cross_visits,
        affinity_matrix,
        store_financials,
    )

    # Train models for each target
    models = {}
    encoders = {}
    cv_results = {}
    for target_col in [
        col.TARGET_CAPTURE_RATE,
        col.TARGET_SALES_PER_SQM,
        col.TARGET_DWELL_TIME,
    ]:
        logger.info(f"Training model for target: {target_col}")
        # TODO: Allow user to select CV strategy
        model, encs, cv_scores = train_performance_model(
            X, y, target_col, mall_ids, cv_strategy="kfold"
        )
        models[target_col] = model
        encoders[target_col] = encs
        cv_results[target_col] = cv_scores

    # Save model artifacts to disk
    save_model_artifacts(models, encoders, mall_means)

    logger.info("Model training pipeline completed.")

    return models, encoders, mall_means, store_codes_order, cv_results


def load_model_artifacts() -> tuple[dict, dict, dict]:
    """Load trained models and related artifacts from disk.

    Returns:
        models: Dictionary mapping target names to trained models.
        encoders: Dictionary mapping target names to their label encoders.
        mall_means: Dictionary mapping target names to mall mean values.
    """
    target_names = [
        col.TARGET_CAPTURE_RATE,
        col.TARGET_SALES_PER_SQM,
        col.TARGET_DWELL_TIME,
    ]

    # Load individual model files
    models = {}
    for target_name in target_names:
        model_path = pth.MODELS_DIR / f"{target_name}_model.joblib"
        logger.info(f"Loading {target_name} model from {model_path}")
        models[target_name] = joblib.load(model_path)

    # Load individual encoder files
    encoders = {}
    for target_name in target_names:
        encoder_path = pth.MODELS_DIR / f"{target_name}_encoders.joblib"
        logger.info(f"Loading {target_name} encoders from {encoder_path}")
        encoders[target_name] = joblib.load(encoder_path)

    # Load mall means from CSV
    logger.info(f"Loading mall means from {pth.MALL_MEANS}")
    mall_means_df = pd.read_csv(pth.MALL_MEANS)
    mall_means = {}
    for target_name in target_names:
        target_rows = mall_means_df[mall_means_df["target"] == target_name]
        mall_means[target_name] = dict(
            zip(target_rows["mall_id"], target_rows["mean_value"], strict=False)
        )

    return models, encoders, mall_means


if __name__ == "__main__":
    training_pipeline()
