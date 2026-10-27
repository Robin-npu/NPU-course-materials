import networkx as nx
import os

def read_packages(filename="package_data.txt"):
    #获取送货清单文件的函数
    packages = []
    print(f"正在读取文件: {filename} ...")

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue

            # 解析格式，例如: "Y6,14kg"
            parts = line.split(',')
            if len(parts) >= 2:
                addr = parts[0].strip()
                # 提取数字重量，去掉 'kg' 并转为 float
                weight_str = parts[1].strip().lower().replace('kg', '')
                try:
                    weight = float(weight_str)
                    packages.append((addr, weight))
                except ValueError:
                    continue
    return packages


def build_campus_graph():
    G = nx.Graph()

    G.add_edge("S", "J_Y", weight=300)
    G.add_edge("J_Y", "J_XH", weight=300)

    G.add_edge("J_Y", "Y_Bot", weight=50)
    G.add_edge("Y_Bot", "Y_Mid", weight=50)
    G.add_edge("Y_Mid", "Y_Top", weight=50)

    # 连接Y区终端点
    for node in ["Y5", "Y6"]: G.add_edge("Y_Bot", node, weight=20)
    for node in ["Y3", "Y4"]: G.add_edge("Y_Mid", node, weight=20)
    for node in ["Y1", "Y2"]: G.add_edge("Y_Top", node, weight=20)

    G.add_edge("J_XH", "X_1", weight=50)
    G.add_edge("X_1", "X_2", weight=50)
    G.add_edge("X_2", "X_3", weight=50)
    G.add_edge("X_3", "X_4", weight=50)

    # 连接X区终端点
    for node in ["X6", "X7"]: G.add_edge("X_1", node, weight=20)
    for node in ["X4", "X5"]: G.add_edge("X_2", node, weight=20)
    for node in ["X2", "X3"]: G.add_edge("X_3", node, weight=20)
    G.add_edge("X_4", "X1", weight=20)

    G.add_edge("J_XH", "H_Hub", weight=800)
    G.add_edge("H_Hub", "H1", weight=20)

    G.add_edge("H_Hub", "H_Mid", weight=100)
    G.add_edge("H_Mid", "H2", weight=20)
    G.add_edge("H_Mid", "H3", weight=20)

    G.add_edge("H_Mid", "H_End", weight=50)
    G.add_edge("H_End", "H4", weight=20)
    G.add_edge("H_End", "H5", weight=20)

    return G


def calculate_cost(G, destinations):
    if not destinations: return 0

    visited_edges = set()
    for dest in destinations:
        try:
            # 在树中，两点间路径是唯一的
            path = nx.shortest_path(G, source="S", target=dest)
            # 记录路径上的边
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge = tuple(sorted((u, v)))  # 排序确保无向边一致
                visited_edges.add(edge)
        except nx.NetworkXNoPath:
            print(f"无法到达地址: {dest}")

    # 单程距离 = 所有经过边的权重之和
    one_way_dist = sum(G[u][v]['weight'] for u, v in visited_edges)
    return one_way_dist * 2  # 往返距离


def solve_delivery_route(G, packages, max_capacity=50):
    if not packages: return
    # 将包裹按 X, Y, H 分组，避免跨区长途折返
    clusters = {'X': [], 'Y': [], 'H': []}
    for addr, weight in packages:
        prefix = addr[0].upper()
        if prefix in clusters:
            clusters[prefix].append((addr, weight))

    all_trips = []

    for region, items in clusters.items():
        # 按重量降序排列 (First Fit Decreasing)
        items.sort(key=lambda x: x[1], reverse=True)

        bins = []
        for item in items:
            item_weight = item[1]
            placed = False
            # 尝试放入已有车次
            for b in bins:
                current_w = sum(p[1] for p in b)
                if current_w + item_weight <= max_capacity:
                    b.append(item)
                    placed = True
                    break
            # 放不下则新开车次
            if not placed:
                bins.append([item])
        all_trips.extend(bins)

    print(f"\n{'=' * 30} 路径规划结果报告 {'=' * 30}")
    print(f"读取文件: package_data.txt | 总包裹数: {len(packages)} | 限重: {max_capacity}kg")
    print(f"{'-' * 75}")
    print(f"{'车次':<4} | {'区域':<5} | {'载重(kg)':<9} | {'往返距离(m)':<9} | {'配送地址清单'}")
    print(f"{'-' * 75}")

    total_distance = 0

    for i, trip in enumerate(all_trips, 1):
        dests = [p[0] for p in trip]
        weight = sum(p[1] for p in trip)
        dist = calculate_cost(G, dests)
        total_distance += dist

        region_name = dests[0][0] + "区"
        dests_str = ", ".join(dests)

        print(f"No.{i:<2} | {region_name:<6} | {weight:<10} | {dist:<12} | {dests_str}")

    print(f"{'-' * 75}")
    print(f"总发车次数: {len(all_trips)} 次")
    print(f"总行驶里程: {total_distance} 米")
    print(f"{'=' * 75}\n")


if __name__ == "__main__":

    package_list = read_packages("package_data.txt")  # 直接读取

    if package_list:
        campus_map = build_campus_graph()
        solve_delivery_route(campus_map, package_list)