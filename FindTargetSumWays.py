import streamlit as st
import networkx as nx
from pyvis.network import Network
import json

def run_target_sum_dfs(nums, target):
    """
    - 构建 (i, cur_sum) 的递归树
    - 用 parent_map 记录父子关系 + 每条边的标签
    - 当 i == len(nums) 时，如果 cur_sum == target，则标记为 valid_leaf
    """
    trace = []              # 存储访问过的节点（unique_id）
    parent_map = {}         # child -> (parent, edge_label)
    valid_leaves = []       # 存储满足 cur_sum == target 的叶子
    ways_count = 0          # 统计达到 target 的方案数

    # 用一个计数器来区分重复出现的 "dfs(i, cur_sum)"
    node_counter = {}       # { "dfs(i,cur_sum)" : 出现次数 }

    def dfs(i, cur_sum, parent_id=None, edge_label=""):
        nonlocal ways_count

        # 1) 生成 base_label（给用户看的）
        base_label = f"dfs({i}, {cur_sum})"
        # 2) 为了保证节点唯一性，加一个内部计数后缀
        if base_label not in node_counter:
            node_counter[base_label] = 0
        node_counter[base_label] += 1

        unique_node_id = f"{base_label}_{node_counter[base_label]}"
        trace.append(unique_node_id)

        # 3) 记录父子关系
        if parent_id is not None:
            parent_map[unique_node_id] = (parent_id, edge_label)

        # 4) 如果到达叶子（i == len(nums)）
        if i == len(nums):
            if cur_sum == target:
                valid_leaves.append(unique_node_id)
                ways_count += 1
            return

        # 5) 分别递归 +nums[i] / -nums[i]
        dfs(i + 1, cur_sum + nums[i], unique_node_id, f"+{nums[i]}")
        dfs(i + 1, cur_sum - nums[i], unique_node_id, f"-{nums[i]}")

    # 从 (0,0) 出发
    dfs(0, 0)

    return trace, parent_map, valid_leaves, ways_count


def create_tree_graph_from_trace(trace, parent_map, valid_leaves):
    """
    构建有向图 + 高亮 valid_leaves 路径上的节点
    """
    G = nx.DiGraph()

    # A) 加入所有节点
    for node_id in trace:
        # 给用户展示的 label 去掉后缀 "_2"
        base_label = node_id.split("_")[0]  # "dfs(i, cur_sum)"
        G.add_node(node_id, base_label=base_label)

    # B) 加入带标签的边
    for child_id, (parent_id, edge_label) in parent_map.items():
        G.add_edge(parent_id, child_id, label=edge_label)

    # C) 高亮所有从 root -> valid_leaf 的路径
    highlighted_nodes = set()

    # 建一个快速索引：child -> parent
    # 其实 parent_map 已经包含，但我们要 parent_id 而不是 (parent_id, label)
    quick_parent = {}
    for c, (p, lbl) in parent_map.items():
        quick_parent[c] = p

    for leaf_id in valid_leaves:
        # 从叶子往上回溯到 root
        cur = leaf_id
        while cur in quick_parent:
            highlighted_nodes.add(cur)
            cur = quick_parent[cur]
        highlighted_nodes.add(cur)  # root

    return G, highlighted_nodes


def plot_graph_with_pyvis(G, highlighted_nodes):
    """
    用 PyVis 绘制有向树，并返回生成的 HTML 文件名 + JSON
    """
    net = Network(notebook=True, height='600px', width='100%')

    # 1) 添加节点
    for node_id, data in G.nodes(data=True):
        label = data["base_label"]
        color = "orange" if node_id in highlighted_nodes else "lightblue"
        net.add_node(node_id, label=label, color=color)

    # 2) 添加边（带标签）
    for (u, v, edge_data) in G.edges(data=True):
        edge_label = edge_data.get("label", "")
        net.add_edge(u, v, label=edge_label)

    # 3) 设置分层布局
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

    # 4) 生成 HTML
    graph_html = "target_sum_tree.html"
    net.save_graph(graph_html)

    # 可选：把节点和边转成 JSON
    js_nodes = []
    for n in net.nodes:
        js_nodes.append({
            "id": n["id"],
            "label": n["label"],
            "color": n["color"]
        })
    js_edges = []
    for (u, v, edata) in G.edges(data=True):
        js_edges.append({
            "from": u, 
            "to": v, 
            "label": edata.get("label", "")
        })

    return graph_html, json.dumps(js_nodes), json.dumps(js_edges)


# -------------------------------
# Streamlit 部分
# -------------------------------
import os
import io

import streamlit as st

st.title("Find Target Sum Ways - DFS Tree")
st.write("""问题描述：给定一个整数数组 nums和一个整数 target。\n
         数组长度不超过 20。向数组中每个整数前加 + 或 -。然后串联起来构造成一个表达式.\n)
要求：返回通过上述方法构造的、运算结果等于 target 的不同表达式数目。\n""")

nums_str = st.text_input("Enter the nums array (comma-separated)", "1,1,1")
target = st.number_input("Enter the target sum:", value=2, step=1)

if st.button("Generate DFS Tree"):
    try:
        nums_list = [int(x.strip()) for x in nums_str.split(",") if x.strip()]
    except:
        st.error("Invalid nums input!")
        st.stop()

    # 1) DFS & 收集信息
    trace, parent_map, valid_leaves, ways_count = run_target_sum_dfs(nums_list, target)

    # 2) 构建有向图，并高亮所有正确路径节点
    G, highlighted_nodes = create_tree_graph_from_trace(trace, parent_map, valid_leaves)

    # 3) PyVis 绘制
    graph_html, js_nodes_json, js_edges_json = plot_graph_with_pyvis(G, highlighted_nodes)

    # 显示方案数
    st.write(f"**Number of ways to reach sum = {target}:** {ways_count}")

    # 4) 把生成的 HTML 嵌入 Streamlit
    with open(graph_html, 'r', encoding='utf-8') as f:
        source_code = f.read()

    st.components.v1.html(source_code, height=600, width=800)