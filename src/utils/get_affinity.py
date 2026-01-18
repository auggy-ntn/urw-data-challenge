"""Category affinity calculation utilities."""

from constants import column_names as col


def create_affinity_results(cross_visits, dim_blocks, fact_stores):
    """Calculates Cosine Similarity scores for store pairs based on cross-visits."""
    # Merge suffixes created by pandas
    cat_high_x = f"{col.CAT_HIGH}_x"
    cat_high_y = f"{col.CAT_HIGH}_y"

    total_cross_visits = cross_visits.merge(
        dim_blocks[[col.STORE_CODE, col.CAT_HIGH]],
        left_on=col.STORE_CODE_1,
        right_on=col.STORE_CODE,
    ).merge(
        dim_blocks[[col.STORE_CODE, col.CAT_HIGH]],
        left_on=col.STORE_CODE_2,
        right_on=col.STORE_CODE,
    )[
        [
            col.STORE_CODE_1,
            col.STORE_CODE_2,
            col.TOTAL_CROSS_VISITS,
            cat_high_x,
            cat_high_y,
        ]
    ]

    grouped_cross_visits = (
        total_cross_visits.groupby([cat_high_x, cat_high_y])
        .agg("sum")[col.TOTAL_CROSS_VISITS]
        .reset_index()
    )

    merged = fact_stores.merge(
        dim_blocks[[col.STORE_CODE, col.CAT_HIGH]],
        left_on=col.STORE_CODE,
        right_on=col.STORE_CODE,
    )[[col.STORE_CODE, col.PEOPLE_IN, col.CAT_HIGH]]

    grouped_visits = (
        merged.groupby(col.CAT_HIGH).agg("sum")[col.PEOPLE_IN].reset_index()
    )
    grouped_visits = grouped_visits.rename(
        columns={col.PEOPLE_IN: "proxy_total_visits", col.CAT_HIGH: "category"}
    )

    df_cosine = grouped_cross_visits.merge(
        grouped_visits, left_on=cat_high_x, right_on="category"
    ).rename(columns={"proxy_total_visits": "size_x"})

    df_cosine = df_cosine.merge(
        grouped_visits, left_on=cat_high_y, right_on="category"
    ).rename(columns={"proxy_total_visits": "size_y"})

    df_cosine["cosine_score"] = (
        10**4
        * df_cosine[col.TOTAL_CROSS_VISITS]
        / ((df_cosine["size_x"] * df_cosine["size_y"]) ** 0.8)
    )

    output = df_cosine[[cat_high_x, cat_high_y, "cosine_score"]].sort_values(
        by="cosine_score", ascending=False
    )
    output = output.rename(
        columns={
            cat_high_x: col.CATEGORY_A,
            cat_high_y: col.CATEGORY_B,
            "cosine_score": col.AFFINITY,
        }
    )
    return output
