# import seaborn as sns
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

# Set up paths
DATA_DIR = Path("data")
OUTPUT_DIR = Path("analysis_output")
OUTPUT_DIR.mkdir(exist_ok=True)


def load_data():
    """Load the necessary datasets."""
    try:
        # Try reading with utf-8 first, fallback to latin1
        read_opts = {"encoding": "utf-8"}

        try:
            dim_blocks = pd.read_csv(DATA_DIR / "dim_blocks_v1.csv", **read_opts)
        except UnicodeDecodeError:
            dim_blocks = pd.read_csv(DATA_DIR / "dim_blocks_v1.csv", encoding="latin1")

        cross_visits_path = DATA_DIR / "cross_visits_v1.csv"
        if not cross_visits_path.exists():
            print(
                f"Warning: {cross_visits_path} not found. Please ensure it is present."
            )
            return None, None, None

        try:
            cross_visits = pd.read_csv(cross_visits_path, **read_opts)
        except UnicodeDecodeError:
            cross_visits = pd.read_csv(cross_visits_path, encoding="latin1")

        try:
            store_financials = pd.read_csv(
                DATA_DIR / "store_financials_v1.csv", **read_opts
            )
        except UnicodeDecodeError:
            store_financials = pd.read_csv(
                DATA_DIR / "store_financials_v1.csv", encoding="latin1"
            )

        return dim_blocks, cross_visits, store_financials
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None, None


def build_graph(cross_visits):
    """Construct undirected graph from cross visits."""
    G = nx.Graph()

    # Add edges with weights
    for _, row in cross_visits.iterrows():
        G.add_edge(
            row["store_code_1"], row["store_code_2"], weight=row["total_cross_visits"]
        )
    return G


def enhance_nodes_and_compute_metrics(G, dim_blocks, store_financials):
    """Add metadata to nodes and calculate metrics."""
    # Merge metadata for easier lookup
    # Assuming store_code in dim_blocks matches nodes
    # store_financials has 'codstr' which matches 'store_code'

    # Metrics calculation
    degree_centrality = nx.degree_centrality(G)
    weighted_degree = dict(G.degree(weight="weight"))
    clustering_coeff = nx.clustering(G, weight="weight")

    # Update node attributes
    for node in G.nodes():
        # Get metadata
        block_info = dim_blocks[dim_blocks["store_code"] == node]
        fin_info = store_financials[store_financials["codstr"] == node]

        if not block_info.empty:
            G.nodes[node]["bl3_label"] = block_info.iloc[0]["bl3_label"]
            G.nodes[node]["gla"] = block_info.iloc[0]["gla"]
        else:
            G.nodes[node]["bl3_label"] = "Unknown"
            G.nodes[node]["gla"] = 0

        if not fin_info.empty:
            G.nodes[node]["sales_r12m"] = fin_info.iloc[0]["sales_r12m"]
        else:
            G.nodes[node]["sales_r12m"] = 0

        # Store metrics on node
        G.nodes[node]["degree_centrality"] = degree_centrality[node]
        G.nodes[node]["weighted_degree"] = weighted_degree[node]
        G.nodes[node]["clustering_coeff"] = clustering_coeff[node]

    return G


def calculate_influence_score_and_summary(G):
    """Calculate Influence Score and Top 10 Summary."""
    # Convert graph data to DataFrame for easier analysis
    node_data = []
    for node, attrs in G.nodes(data=True):
        data = {"store_code": node}
        data.update(attrs)
        node_data.append(data)

    df_nodes = pd.DataFrame(node_data)

    # Define Influence Score
    # Custom metric: let's define it as a combination of weighted degree
    # (flow volume) and degree centrality (reach)
    # Normalized to be comparable
    if not df_nodes.empty:
        df_nodes["norm_weighted_degree"] = (
            df_nodes["weighted_degree"] / df_nodes["weighted_degree"].max()
        )
        df_nodes["norm_degree_centrality"] = (
            df_nodes["degree_centrality"] / df_nodes["degree_centrality"].max()
        )

        # Simple weighted average
        df_nodes["influence_score"] = (0.7 * df_nodes["norm_weighted_degree"]) + (
            0.3 * df_nodes["norm_degree_centrality"]
        )

        top_10 = df_nodes.sort_values("influence_score", ascending=False).head(10)
        return df_nodes, top_10
    return pd.DataFrame(), pd.DataFrame()


def create_synergy_matrix(cross_visits, dim_blocks):
    """Create Synergy Matrix by category (bl3_label)."""
    # Map stores to categories
    store_cat_map = dict(
        zip(dim_blocks["store_code"], dim_blocks["bl3_label"], strict=False)
    )

    # Add categories to cross_visits
    df = cross_visits.copy()
    df["cat_1"] = df["store_code_1"].map(store_cat_map)
    df["cat_2"] = df["store_code_2"].map(store_cat_map)

    # Drop rows where category is missing
    df = df.dropna(subset=["cat_1", "cat_2"])

    # Aggregate
    # summing total visits between categories and dividing by count of links or similar?
    # User asked for "average number of cross-visits", so mean()

    # Sort categories to ensure (A, B) is same as (B, A) for grouping if directed,
    # but here we have explicit pairs
    # Assuming cross_visits might be undirected (A-B) or directed.
    # Usually provided as unique pairs.
    # Let's treat (cat_1, cat_2) as a pair.

    # We need to make sure Cat A - Cat B includes both Cat A -> Cat B
    # and Cat B -> Cat A directions if the data separates them
    # OR just group by sorted tuple.

    # For a Matrix, we want a Pivot Table.

    synergy_df = (
        df.groupby(["cat_1", "cat_2"])["total_cross_visits"].mean().reset_index()
    )

    # Pivot
    matrix = synergy_df.pivot(
        index="cat_1", columns="cat_2", values="total_cross_visits"
    )

    return matrix


def main():
    """Main function to run the analysis."""
    print("Loading data...")
    dim_blocks, cross_visits, store_financials = load_data()

    if dim_blocks is None or cross_visits is None:
        print("Data load failed. Exiting.")
        return

    print("Building graph...")
    G = build_graph(cross_visits)

    print("Enhancing nodes and computing metrics...")
    G = enhance_nodes_and_compute_metrics(G, dim_blocks, store_financials)

    print("Calculating influence scores...")
    df_nodes, top_10 = calculate_influence_score_and_summary(G)

    print("\nTop 10 Stores by Influence Score:")
    print(
        top_10[
            [
                "store_code",
                "bl3_label",
                "weighted_degree",
                "degree_centrality",
                "influence_score",
            ]
        ]
    )
    top_10.to_csv(OUTPUT_DIR / "top_10_stores.csv", index=False)

    print("Creating Synergy Matrix...")
    synergy_matrix = create_synergy_matrix(cross_visits, dim_blocks)

    # Plotting
    plt.figure(figsize=(12, 10))
    # Select top 10 categories by total interaction volume for readable heatmap
    # if too large
    # For now, plot all or top N based on matrix size

    # If matrix is huge, subset it.
    if synergy_matrix.shape[0] > 20:
        # Filter for top categories
        top_cats = (
            synergy_matrix.sum(axis=1).sort_values(ascending=False).head(10).index
        )
        plot_matrix = synergy_matrix.loc[top_cats, top_cats]
    else:
        plot_matrix = synergy_matrix

    # sns.heatmap(plot_matrix, annot=True, fmt='.1f', cmap='viridis')
    plt.imshow(plot_matrix, cmap="viridis", aspect="auto")
    plt.colorbar(label="Avg Cross-Visits")

    # Add labels
    plt.xticks(range(len(plot_matrix.columns)), plot_matrix.columns, rotation=90)
    plt.yticks(range(len(plot_matrix.index)), plot_matrix.index)

    # Annotate
    for i in range(len(plot_matrix.index)):
        for j in range(len(plot_matrix.columns)):
            plt.text(
                j,
                i,
                f"{plot_matrix.iloc[i, j]:.1f}",
                ha="center",
                va="center",
                color="w",
            )
    plt.title("Category Synergy Matrix (Avg Cross-Visits)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "synergy_heatmap.png")
    print(f"Heatmap saved to {OUTPUT_DIR / 'synergy_heatmap.png'}")


if __name__ == "__main__":
    main()
