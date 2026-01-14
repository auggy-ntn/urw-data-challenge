import pandas as pd


# 1. Define Jaccard Calculation Function
def calculate_jaccard(df):
    """Calculates the Jaccard Similarity Index based solely on cross-visit volume."""
    # Create a copy to avoid SettingWithCopy warnings on the original dataframe
    df = df.copy()

    # Calculate "Proxy Totals" (Network Footprint) for each store
    all_visits = pd.concat(
        [
            df[["store_code_1", "total_cross_visits"]].rename(
                columns={"store_code_1": "store_id"}
            ),
            df[["store_code_2", "total_cross_visits"]].rename(
                columns={"store_code_2": "store_id"}
            ),
        ]
    )

    # Group by store ID to get the total sum of all cross-visits involving this store
    store_sums = all_visits.groupby("store_id")["total_cross_visits"].sum()

    # Map these totals back to the original dataframe
    df["sum_1"] = df["store_code_1"].map(store_sums)
    df["sum_2"] = df["store_code_2"].map(store_sums)

    # Calculate Jaccard Score
    # Formula: Intersection / (Total_A + Total_B - Intersection)
    union = df["sum_1"] + df["sum_2"] - df["total_cross_visits"]

    # Vectorized approach (cleaner)
    mask = union > 0
    df.loc[mask, "jaccard_score"] = df.loc[mask, "total_cross_visits"] / union.loc[mask]
    df.loc[~mask, "jaccard_score"] = 0

    # Cleanup
    df.drop(columns=["sum_1", "sum_2"], inplace=True)

    return df.sort_values(by="jaccard_score", ascending=False)


# 2. Define Category Affinity Function
def calculate_category_affinity(jaccard_df, dim_block_df):
    """Aggregates store-to-store Jaccard scores into category-to-category affinities."""
    # Merge Category for Store 1
    df_merged = jaccard_df.merge(
        dim_block_df[["store_code", "bl1_label"]],
        left_on="store_code_1",
        right_on="store_code",
        how="inner",
    ).rename(columns={"bl1_label": "category_1"})

    df_merged.drop(columns=["store_code"], inplace=True)

    # Merge Category for Store 2
    df_merged = df_merged.merge(
        dim_block_df[["store_code", "bl1_label"]],
        left_on="store_code_2",
        right_on="store_code",
        how="inner",
    ).rename(columns={"bl1_label": "category_2"})

    df_merged.drop(columns=["store_code"], inplace=True)

    # Create unified "Pair" identifier
    df_merged["category_pair"] = df_merged.apply(
        lambda x: tuple(sorted([str(x["category_1"]), str(x["category_2"])])), axis=1
    )

    # Aggregate by Category Pair
    category_affinity = (
        df_merged.groupby("category_pair")["jaccard_score"]
        .agg(["mean", "count", "sum"])
        .reset_index()
    )

    # Split the tuple back into two columns
    category_affinity[["cat_A", "cat_B"]] = pd.DataFrame(
        category_affinity["category_pair"].tolist(), index=category_affinity.index
    )

    # Rename for clarity
    category_affinity = category_affinity.rename(
        columns={
            "mean": "avg_jaccard_strength",
            "count": "number_of_pairs",
            "sum": "total_interaction_volume",
        }
    )

    return category_affinity[
        ["cat_A", "cat_B", "avg_jaccard_strength", "number_of_pairs"]
    ].sort_values(by="avg_jaccard_strength", ascending=False)


def create_affinity_results(cross_visits_df, dim_block_df):
    """Wrapper function to create category affinity results from cross-visit data."""
    jaccard_results = calculate_jaccard(cross_visits_df)
    affinity_results = calculate_category_affinity(jaccard_results, dim_block_df)
    return affinity_results
