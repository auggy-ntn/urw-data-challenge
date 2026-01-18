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
    # Custom metric: combination of weighted degree (flow) and degree centrality (reach)
    if not df_nodes.empty:
        df_nodes["norm_weighted_degree"] = (
            df_nodes["weighted_degree"] / df_nodes["weighted_degree"].max()
        )
        df_nodes["norm_degree_centrality"] = (
            df_nodes["degree_centrality"] / df_nodes["degree_centrality"].max()
        )

        df_nodes["influence_score"] = (0.7 * df_nodes["norm_weighted_degree"]) + (
            0.3 * df_nodes["norm_degree_centrality"]
        )

        top_15 = df_nodes.sort_values("influence_score", ascending=False).head(15)
        return df_nodes, top_15
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

    # Aggregate: Average cross-visits
    synergy_df = (
        df.groupby(["cat_1", "cat_2"])["total_cross_visits"].mean().reset_index()
    )

    # Pivot
    matrix = synergy_df.pivot(
        index="cat_1", columns="cat_2", values="total_cross_visits"
    )

    return matrix


def plot_category_network_graph(cross_visits, dim_blocks, output_path):
    """Plot the network graph with Categories as nodes."""
    print("Generating category network graph...")

    # Map stores to categories
    store_cat_map = dict(
        zip(dim_blocks["store_code"], dim_blocks["bl3_label"], strict=False)
    )

    # Prepare data
    df = cross_visits.copy()
    df["cat_1"] = df["store_code_1"].map(store_cat_map)
    df["cat_2"] = df["store_code_2"].map(store_cat_map)
    df = df.dropna(subset=["cat_1", "cat_2"])

    # Aggregate cross-visits by category pair (undirected)
    # Create a sorted tuple to treat (A, B) and (B, A) as the same edge
    df["pair"] = df.apply(lambda x: tuple(sorted([x["cat_1"], x["cat_2"]])), axis=1)

    # Group and sum
    agg_df = df.groupby("pair")["total_cross_visits"].sum().reset_index()

    # Build Graph
    G = nx.Graph()
    for _, row in agg_df.iterrows():
        u, v = row["pair"]
        w = row["total_cross_visits"]
        if u != v:  # Skip self-loops for cleaner visualization
            G.add_edge(u, v, weight=w)

    # Compute Node Metrics for Sizing
    # Size by Weighted Degree (Total Traffic)
    weighted_degree = dict(G.degree(weight="weight"))
    if not weighted_degree:
        print("Graph is empty.")
        return

    # Normalize sizes
    max_deg = max(weighted_degree.values())
    node_sizes = [5000 * (weighted_degree[n] / max_deg) + 100 for n in G.nodes()]

    # Normalize edge widths
    weights = [G.edges[e]["weight"] for e in G.edges()]
    max_weight = max(weights) if weights else 1
    edge_widths = [15 * (w / max_weight) + 0.5 for w in weights]

    # Plot
    plt.figure(figsize=(15, 15))
    pos = nx.spring_layout(G, k=2.0, seed=42)  # High k for spatial separation

    # Draw Nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=node_sizes,
        node_color="skyblue",
        alpha=0.9,
        edgecolors="white",
    )

    # Draw Edges
    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.6, edge_color="navy")

    # Draw Labels with background box for readability
    # labels = {n: n for n in G.nodes()}
    # Draw labels manually to add bbox
    for node, (x, y) in pos.items():
        plt.text(
            x,
            y,
            node,
            fontsize=9,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.7),
        )

    plt.title("Category Synergy Network (Node Size = Total Traffic)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Network graph saved to {output_path}")


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
    df_nodes, top_15 = calculate_influence_score_and_summary(G)

    print("\\nTop 15 Stores by Influence Score:")
    print(
        top_15[
            [
                "store_code",
                "bl3_label",
                "weighted_degree",
                "degree_centrality",
                "influence_score",
            ]
        ]
    )
    top_15.to_csv(OUTPUT_DIR / "top_15_stores.csv", index=False)
    df_nodes.to_csv(OUTPUT_DIR / "df_nodes.csv", index=False)

    # Visualize Network Graph
    print("Visualizing Category Network Graph...")
    plot_category_network_graph(
        cross_visits, dim_blocks, OUTPUT_DIR / "category_network_graph.png"
    )

    print("Creating Synergy Matrix...")
    synergy_matrix = create_synergy_matrix(cross_visits, dim_blocks)

    # Plotting Heatmap
    plt.figure(figsize=(12, 10))
    if synergy_matrix.shape[0] > 20:
        # Filter for top categories
        top_cats = (
            synergy_matrix.sum(axis=1).sort_values(ascending=False).head(10).index
        )
        plot_matrix = synergy_matrix.loc[top_cats, top_cats]
    else:
        plot_matrix = synergy_matrix

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
