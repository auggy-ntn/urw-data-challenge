def create_affinity_results(cross_visits, dim_blocks, fact_stores):
    """Calculates Cosine Similarity scores for store pairs based on cross-visits."""
    total_cross_visits = cross_visits.merge(
        dim_blocks[["store_code", "bl1_label"]],
        left_on="store_code_1",
        right_on="store_code",
    ).merge(
        dim_blocks[["store_code", "bl1_label"]],
        left_on="store_code_2",
        right_on="store_code",
    )[
        [
            "store_code_1",
            "store_code_2",
            "total_cross_visits",
            "bl1_label_x",
            "bl1_label_y",
        ]
    ]

    grouped_cross_visits = (
        total_cross_visits.groupby(["bl1_label_x", "bl1_label_y"])
        .agg("sum")["total_cross_visits"]
        .reset_index()
    )

    merged = fact_stores.merge(
        dim_blocks[["store_code", "bl1_label"]],
        left_on="store_code",
        right_on="store_code",
    )[["store_code", "people_in", "bl1_label"]]

    grouped_visits = merged.groupby("bl1_label").agg("sum")["people_in"].reset_index()
    grouped_visits = grouped_visits.rename(
        columns={"people_in": "proxy_total_visits", "bl1_label": "category"}
    )

    df_cosine = grouped_cross_visits.merge(
        grouped_visits, left_on="bl1_label_x", right_on="category"
    ).rename(columns={"proxy_total_visits": "size_x"})

    df_cosine = df_cosine.merge(
        grouped_visits, left_on="bl1_label_y", right_on="category"
    ).rename(columns={"proxy_total_visits": "size_y"})

    df_cosine["cosine_score"] = (
        10**4
        * df_cosine["total_cross_visits"]
        / ((df_cosine["size_x"] * df_cosine["size_y"]) ** 0.8)
    )

    output = df_cosine[["bl1_label_x", "bl1_label_y", "cosine_score"]].sort_values(
        by="cosine_score", ascending=False
    )
    output.rename(
        columns={
            "bl1_label_x": "cat_A",
            "bl1_label_y": "cat_B",
            "cosine_score": "similarity_score",
        },
        inplace=True,
    )
    return output
