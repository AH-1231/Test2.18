import streamlit as st
import networkx as nx
from pyvis.network import Network
import json

def run_knapsack_dfs(weight, value, W):
    """
    Build a 0/1 Knapsack recursion tree:
    - We track (i, w, v): item index, remaining capacity, total value so far
    - Two edges from each node:
      1) Skip item i
      2) Pick item i (if w >= weight[i])
    - Return a trace of all unique node-IDs + a parent_map with edge labels
    """
    trace = []
    parent_map = {}
    node_counter = {}  # For differentiating multiple visits of same (i, w, v)

    def dfs(i, w, v, parent_id=None, edge_label=""):
        # 1) Create a base label to display: dp(i, w, v)
        base_label = f"dp({i},{w},{v})"

        # 2) Ensure unique node-ID by appending a counter
        if base_label not in node_counter:
            node_counter[base_label] = 0
        node_counter[base_label] += 1
        unique_node_id = f"{base_label}_{node_counter[base_label]}"

        # 3) Record this node
        trace.append(unique_node_id)

        # 4) Connect to parent with an edge label
        if parent_id is not None:
            parent_map[unique_node_id] = (parent_id, edge_label)

        # 5) If we've considered all items, stop
        if i >= len(weight):
            return

        # 6) Branch 1: Skip item i
        dfs(i + 1, w, v, unique_node_id, f"Skip item {i}")

        # 7) Branch 2: Pick item i (if capacity allows)
        if w >= weight[i]:
            dfs(i + 1, w - weight[i], v + value[i], unique_node_id, f"Pick item {i}")

    # Start recursion from i=0, capacity=W, value=0
    dfs(0, W, 0)

    return trace, parent_map

def create_tree_graph_from_trace(trace, parent_map):
    """
    Build a directed graph from the DFS trace + parent_map
    - Each node has an internal ID with _counter suffix
    - We display only dp(i,w,v) to the user
    - Edges labeled "Pick item i" or "Skip item i"
    """
    G = nx.DiGraph()

    # Add nodes
    for node_id in trace:
        # Remove the "_2" suffix for display
        base_label = node_id.split("_")[0]  # e.g. "dp(0,5,0)"
        G.add_node(node_id, display_label=base_label)

    # Add edges with label
    for child_id, (parent_id, edge_label) in parent_map.items():
        G.add_edge(parent_id, child_id, label=edge_label)

    return G

def plot_graph_with_pyvis(G):
    """
    Use PyVis to render the graph in a hierarchical layout
    """
    net = Network(notebook=True, height='600px', width='100%')

    # Add nodes
    for node_id, data in G.nodes(data=True):
        label = data["display_label"]  # e.g. "dp(0,5,0)"
        net.add_node(node_id, label=label, color="lightblue")

    # Add edges with label
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

    # Export to HTML
    graph_html = "knapsack_tree.html"
    net.save_graph(graph_html)

    # Also build JSON if needed for advanced usage
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
import streamlit as st

st.title("0/1 Knapsack Recursion Tree Visualization")

weight_str = st.text_input("Enter weights (comma-separated)", "2,3,4")
value_str = st.text_input("Enter values (comma-separated)", "3,4,5")
W = st.number_input("Enter the backpack capacity (W)", value=5, step=1)

if st.button("Generate Tree"):
    try:
        weight_list = [int(x.strip()) for x in weight_str.split(",") if x.strip()]
        value_list = [int(x.strip()) for x in value_str.split(",") if x.strip()]
    except:
        st.error("Invalid weight/value input!")
        st.stop()

    if len(weight_list) != len(value_list):
        st.error("weight and value arrays must have the same length!")
        st.stop()

    # 1) Build recursion trace
    trace, parent_map = run_knapsack_dfs(weight_list, value_list, W)

    # 2) Create networkx graph
    G = create_tree_graph_from_trace(trace, parent_map)

    # 3) Render with PyVis
    graph_html, js_nodes_json, js_edges_json = plot_graph_with_pyvis(G)

    # 4) Display in Streamlit
    with open(graph_html, 'r', encoding='utf-8') as f:
        source_code = f.read()

    st.components.v1.html(source_code, height=600, width=800)