import streamlit as st
import networkx as nx
from pyvis.network import Network
import json

def build_knapsack_dp_table(weight, value, W):
    """
    Build the DP table for 0/1 Knapsack using the formula:
      dp[i][w] = max(dp[i-1][w], dp[i-1][w-weight[i-1]] + value[i-1])
    where i in [1..n], w in [0..W].
    dp[i][w] represents the max value using the first i items (index 0..i-1).
    
    Returns:
      dp: 2D list of shape (n+1) x (W+1)
    """
    n = len(weight)
    dp = [[0]*(W+1) for _ in range(n+1)]

    for i in range(1, n+1):
        for w in range(W+1):
            # Not picking item (i-1)
            dp[i][w] = dp[i-1][w]
            # If we can pick item (i-1)
            if w >= weight[i-1]:
                pick_val = dp[i-1][w - weight[i-1]] + value[i-1]
                if pick_val > dp[i][w]:
                    dp[i][w] = pick_val
    return dp

def build_dp_graph(dp, weight, value):
    """
    Build a directed graph from the DP table in a top-down manner:
      - Node for dp(i, w) labeled "dp(i,w)=X"
      - From dp(i, w), check how dp(i+1, ...) is derived:
         dp[i+1][w] == dp[i][w]  => "skip item i" edge
         dp[i+1][w-weight[i]] == dp[i][w] + value[i] => "pick item i"
      - We do this for i in [0..n-1], w in [0..W].
      - The root is dp(0, W). The leaves are dp(n, w) for w in [0..W].
    
    Returns:
      G (nx.DiGraph)
    """
    G = nx.DiGraph()
    n = len(dp) - 1  # number of items
    W = len(dp[0]) - 1

    # We'll keep a dictionary to store the unique node_id for each (i, w)
    node_id_map = {}
    node_counter = 0

    def get_node_id(i, w):
        """Return a unique ID for dp(i, w), create if not exist."""
        nonlocal node_counter
        if (i, w) not in node_id_map:
            node_id_map[(i, w)] = node_counter
            node_counter += 1
        return node_id_map[(i, w)]

    # 1) Add nodes for all dp(i,w)
    for i in range(n+1):
        for w in range(W+1):
            node_label = f"dp({i},{w})={dp[i][w]}"
            nid = get_node_id(i, w)
            G.add_node(nid, label=node_label)

    # 2) Add edges from dp(i,w) -> dp(i+1, ...)
    for i in range(n):
        for w in range(W+1):
            cur_val = dp[i][w]
            nid_parent = get_node_id(i, w)

            # 2A) Check skip
            # If dp[i+1][w] == dp[i][w], then we can skip item i
            if dp[i+1][w] == cur_val:
                nid_child = get_node_id(i+1, w)
                G.add_edge(nid_parent, nid_child, label=f"skip item {i}")

            # 2B) Check pick
            # If w >= weight[i] and dp[i+1][w] == dp[i][w-weight[i]] + value[i]
            if w >= weight[i]:
                pick_val = dp[i][w - weight[i]] + value[i]
                if dp[i+1][w] == pick_val:
                    nid_child = get_node_id(i+1, w)
                    G.add_edge(nid_parent, nid_child, label=f"pick item {i}")

    return G

def plot_graph_pyvis(G):
    """
    Render the graph in a hierarchical layout using PyVis,
    and return the generated HTML file path + JSON for advanced usage.
    """
    net = Network(notebook=True, height='600px', width='100%')

    # Add nodes
    for nid, data in G.nodes(data=True):
        net.add_node(nid, label=data['label'], color="lightblue")

    # Add edges (with labels)
    for (u, v, edge_data) in G.edges(data=True):
        edge_label = edge_data.get("label", "")
        net.add_edge(u, v, label=edge_label)

    # Hierarchical layout
    net.set_options('''
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "levelSeparation": 150,
          "nodeSpacing": 100,
          "treeSpacing": 200,
          "direction": "UD",
          "sortMethod": "directed"
        }
      },
      "edges": {
        "smooth": {
          "type": "continuous"
        }
      },
      "physics": {
        "enabled": false
      }
    }
    ''')

    graph_html = "knapsack_dp_tree.html"
    net.save_graph(graph_html)

    # Also create JSON for potential custom usage
    js_nodes = []
    for n in net.nodes:
        js_nodes.append({
            "id": n["id"],
            "label": n["label"],
            "color": n["color"]
        })
    js_edges = []
    for (u, v, edata) in G.edges(data=True):
        js_edges.append({"from": u, "to": v, "label": edata.get("label", "")})

    return graph_html, json.dumps(js_nodes), json.dumps(js_edges)

# -------------------------------
# Streamlit app
# -------------------------------
def main():
    st.title("0/1 Knapsack DP Visualization (Top-Down Graph)")

    weight_str = st.text_input("Enter weights (comma-separated)", "2,3,4")
    value_str = st.text_input("Enter values (comma-separated)", "3,4,5")
    W = st.number_input("Enter the backpack capacity (W)", value=5, step=1)

    if st.button("Generate DP Graph"):
        try:
            weight_list = [int(x.strip()) for x in weight_str.split(",") if x.strip()]
            value_list = [int(x.strip()) for x in value_str.split(",") if x.strip()]
        except:
            st.error("Invalid weight/value input!")
            return

        if len(weight_list) != len(value_list):
            st.error("weight and value arrays must have the same length!")
            return

        # 1) Build DP table
        dp = build_knapsack_dp_table(weight_list, value_list, W)

        # 2) Build the DP graph
        G = build_dp_graph(dp, weight_list, value_list)

        # 3) PyVis plot
        graph_html, js_nodes_json, js_edges_json = plot_graph_pyvis(G)

        # 4) Embed in Streamlit
        with open(graph_html, 'r', encoding='utf-8') as f:
            source_code = f.read()

        st.components.v1.html(source_code, height=600, width=800)

if __name__ == "__main__":
    import sys
    if "streamlit" in sys.modules:
        # If running via "streamlit run KnapsackDP_Protocol.py"
        main()
    else:
        # If running as plain Python (for testing)
        print("Please run via: streamlit run KnapsackDP_Protocol.py")