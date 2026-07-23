#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import numpy as np
import networkx as nx
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from queue import Queue
import sys


def get_time_windows(all_edges, windows_num):
    min_time = float(all_edges[0][3]['start_time'])
    max_time = float(all_edges[len(all_edges) - 1][3]['start_time'])
    windows_time = (max_time - min_time) / windows_num
    windows_graph_dict = {}
    now_time = min_time + windows_time
    for i in range(windows_num):
        now_time += (windows_time * i)
        windows_graph_dict[now_time] = nx.MultiDiGraph()
    for e in all_edges:
        source, target, key, attr = e
        time1 = float(attr['start_time'])
        flag= True
        for key in windows_graph_dict.keys():
            if time1 <= key: # The event is within the time window.
                windows_graph_dict[key].add_edge(source, target, type=attr['type'])
                flag = False
                break
        if flag:
            # The event exceeds the largest time window; add it to the final window.
            windows_graph_dict[now_time].add_edge(source, target, type=attr['type'])
    return windows_graph_dict


def get_idf(back_graph, windows_graph_dict):
    idf = {}
    N = len(windows_graph_dict.keys())
    
    for node in back_graph.nodes():
        Nv = 0
        for key in windows_graph_dict.keys():
            graph = windows_graph_dict[key]
            if node in graph.nodes():
                Nv += 1
                
        idf[node] = np.log(N / (Nv + 1))
    return idf


def feature_extraction_without_idf(back_graph, poi_event):
    """
    Extract features.
    :param back_graph:
    :param poi_event: ls [u, v, key]
    :param idf: IDF score.
    :return: weights: List containing [fs, ft, fc], with each row corresponding to an edge in all_edges.
    """
    # 378203 -> 378224 [ label="43137993" amount="50781" time="1523300798000" id="43137993" type="write" ];
    # powershell.exe_7784
    # data/update.ps1
    # poi_node = 'data/update.ps1'
    # poi_time = 1523300798000
    u, v, key = poi_event[0], poi_event[1], poi_event[2]
    poi_ses = int(back_graph.adj[u][v][key]['data_amount']) # 50781
    poi_tes = float(back_graph.adj[u][v][key]['end_time']) # 1523300798000
    # Add fs, ft, and fc to each edge and store them in the weights list.
    weights = []
    # all_edges = list(back_graph.edges(data=True, keys=True))
    all_edges = sorted(back_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    # min_time = all_edges[0][3]['start_time']
    # max_time = all_edges[len(all_edges) - 1][3]['start_time']
    graph = nx.MultiDiGraph()
    for i in range(len(list(all_edges))):
        edge = all_edges[i]
        source, target, key, attr = edge
        type1 = attr['type']
        fs = 1 / (abs(int(attr['data_amount']) - poi_ses) + 1e-4)
        ft = np.log(1 + 1 / (abs(float(attr['end_time']) - poi_tes) + 1e-10))
        fc = back_graph.out_degree(target) / back_graph.in_degree(target)
        weights.append([fs, ft, fc])
    # print('weights: \n', weights)
    return weights


def feature_extraction(back_graph, poi_event, idf, need_idf=True):
    """
    Extract features.
    :param back_graph:
    :param poi_event: ls [u, v, key]
    :param idf: IDF score.
    :return: weights: List containing [fs, ft, fc], with each row corresponding to an edge in all_edges.
    """
    # 378203 -> 378224 [ label="43137993" amount="50781" time="1523300798000" id="43137993" type="write" ];
    # powershell.exe_7784
    # data/update.ps1
    # poi_node = 'data/update.ps1'
    # poi_time = 1523300798000
    u, v, key = poi_event[0], poi_event[1], poi_event[2]
    poi_ses = int(back_graph.adj[u][v][key]['data_amount']) # 50781
    poi_tes = float(back_graph.adj[u][v][key]['end_time']) # 1523300798000
    # Add fs, ft, and fc to each edge and store them in the weights list.
    weights = []
    all_edges = sorted(back_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))

    graph = nx.MultiDiGraph()
    for i in range(len(list(all_edges))):
        edge = all_edges[i]
        source, target, key, attr = edge
        type1 = attr['type']
        fs = 1 / (abs(int(attr['data_amount']) - poi_ses) + 1e-4)
        ft = np.log(1 + 1 / (abs(float(attr['end_time']) - poi_tes) + 1e-10))
        fc = back_graph.out_degree(target) / back_graph.in_degree(target)
        # Event frequency - 1 IDF: ln(N / (Nv + 1)).
        if need_idf:
            idf_score = idf[target]
            weights.append([fs, ft, fc, idf_score])
        else:
            weights.append([fs, ft, fc])
    return weights


# Define the K-means++ initialization function.
def kmeans_plus_plus_initialization(X, n_clusters):
    n_samples, n_features = X.shape
    centers = np.empty((n_clusters, n_features), dtype=X.dtype)

    # Select an initial centroid at random.
    initial_center = X[np.random.randint(0, n_samples)]
    centers[0] = initial_center

    for i in range(1, n_clusters):
        # Calculate the squared distance from each point to its nearest centroid.
        distances = np.array([min(np.linalg.norm(center - x) ** 2 for center in centers[:i]) for x in X])
        # Select the next centroid probabilistically.
        probabilities = distances / distances.sum()
        next_center_index = np.random.choice(n_samples, p=probabilities)
        centers[i] = X[next_center_index]

    return centers


# Multi-K-means++ function.
def multi_kmeans_plus_plus(X, n_clusters, num_initializations):
    best_kmeans = None
    best_inertia = float('inf')
    # Run K-means clustering with K-means++ initialization.
    # n_clusters = 2
    for i in range(num_initializations):
        initial_centers = kmeans_plus_plus_initialization(X, n_clusters)
        kmeans = KMeans(n_clusters=n_clusters, init=initial_centers, n_init=1, random_state=0)
        kmeans.fit(X)

        # Calculate inertia (total within-cluster variance) as the clustering-quality metric.
        inertia = kmeans.inertia_
        # print(inertia)
        # Update the best clustering result.
        if inertia < best_inertia:
            best_inertia = inertia
            best_kmeans = kmeans

    # # Get cluster centroids and assignments.
    # cluster_centers = kmeans.cluster_centers_
    # labels = kmeans.labels_
    # print(cluster_centers)
    # print(labels)
    return best_kmeans


def weight_computation_without_lda(back_graph, weights):
    """Calculate weights without using LDA.
    
    :param back_graph:
    :param weights:
    :return: back_graph: Backward dependency graph with edge weights.
    """
    all_nodes = back_graph.nodes(data=True)
    all_nodes_list = list(back_graph.nodes(data=True))
    weight_euv = []
    for i in weights:
        # print(i)
        # w = i[0] + i[1] + i[2] + i[3]
        w = 0
        for j in i:
            w += j
        weight_euv.append(w)
    back_graph_adj = back_graph.adj
    all_edges = list(back_graph.edges(data=True, keys=True))
    # Add the previously calculated weight to each edge.
    for i in range(len(all_edges)):
        source, target, key, attr = all_edges[i]
        back_graph_adj[source][target][key]['weight'] = weight_euv[i]

    # Sum each node's outgoing-edge weights and assign the result as the node weight.
    for i in range(len(all_nodes_list)):
        node_name = all_nodes_list[i][0]
        weight_sum = 0
        for j in back_graph_adj[node_name].keys():
            for k in back_graph_adj[node_name][j].keys():
                weight_sum += back_graph_adj[node_name][j][k]['weight']
        all_nodes[node_name]['weight'] = weight_sum
    # This should be all_nodes. Both all_nodes and all_nodes_list are references, so changing all_nodes also changes all_nodes_list.
    # print('back_graph.nodes = ', back_graph.nodes(data=True))
    # print('all_nodes_list = ', all_nodes_list)
    # Finally, calculate each edge's normalized weight.
    for i in range(len(all_nodes_list)):
        node_name = all_nodes_list[i][0]
        weight_sum = all_nodes_list[i][1]['weight']
        for j in back_graph_adj[node_name].keys():
            for k in back_graph_adj[node_name][j].keys():
                back_graph_adj[node_name][j][k]['weight'] = back_graph_adj[node_name][j][k]['weight'] / weight_sum
    return back_graph


def weight_computation(back_graph, weights, not_use_lda=True):
    """

    :param back_graph:
    :param weights:
    :return: back_graph: Backward dependency graph with edge weights.
    """
    '''
        2.3 Dependency-weight calculation
        Step 1: Edge clustering
        First scale features to the [0, 1] range, then use Multi-K-means++ to form two clusters.
    '''
    # Scale to the [0, 1] range.
    # Create a MinMaxScaler object.
    scaler = MinMaxScaler()
    # Standardize features with fit_transform.
    scaled_weights = scaler.fit_transform(weights)
    # print("scaled_weights : \n", scaled_weights)

    # Multi-K-means++ clustering.
    # Specify the number of clusters and initialization runs.
    num_clusters = 2
    num_initializations = 10

    # Call the Multi-K-means++ function.
    best_kmeans = multi_kmeans_plus_plus(scaled_weights, num_clusters, num_initializations)

    # Get the clustering result.
    labels = best_kmeans.labels_
    # print("Clustering result:", labels)
    '''
        Step 2: Discriminative feature projection
    '''

    # Create the LDA model.
    lda = LinearDiscriminantAnalysis()  # n_components is the target dimensionality.
    # Train the LDA model.
    lda.fit(scaled_weights, labels)  # X contains feature data; y contains class labels.
    weight_f = lda.coef_
    # print('weight_f : \n', weight_f)

    # -1.38117461e-01 -1.60216035e+14 -1.35396085e+00
    # 1.38117453e-01 1.60216035e+14 1.35396085e+00
    weight_euv = []
    for i in weights:
        # print(i)
        # w = i[0] * weight_f[0][0] + i[1] * weight_f[0][1] + i[2] * weight_f[0][2] + i[3] * weight_f[0][3]
        w = 0
        for j in range(len(i)):
            w += i[j] * weight_f[0][j]
        weight_euv.append(w)

    # print('weight_euv : \n', weight_euv)

    # Count the ones.
    count_1 = len([label for label in labels if label == 1])  # labels.count(1)
    # Count the zeros.
    count_0 = len([label for label in labels if label == 0])  # labels.count(0)
    # print("Number of ones:", count_1)
    # print("Number of zeros:", count_0)

    little_class = -1
    if count_0 < count_1:
        little_class = 0
        # print('0 is the minority class')
    else:
        little_class = 1
        # print('1 is the minority class')

    little_class_sum = sum(euv for euv, label in zip(weight_euv, labels) if label == little_class)
    other_sum = sum(weight_euv) - little_class_sum
    # print("little_class_sum = ", little_class_sum)
    # print('other_sum = ', other_sum)

    # This appears intended to make critical-edge weights greater than non-critical-edge weights, as described below.
    # If the smaller edge group (possibly the critical-edge group) has a lower mean projected weight, negate the projection vector.
    if other_sum > little_class_sum:
        # print('less than')
        for i in range(len(weights)):
            # print(i)
            # w = weights[i][0] * weight_f[0][0] + weights[i][1] * weight_f[0][1] + weights[i][2] * weight_f[0][2]
            if labels[i] != little_class:
                # w = -1 * w
                weight_euv[i] = -1 * weight_euv[i]
    # print('weight_euv : \n', weight_euv)

    little_class_sum = sum(euv for euv, label in zip(weight_euv, labels) if label == little_class)
    other_sum = sum(weight_euv) - little_class_sum
    # print("little_class_sum = ", little_class_sum)
    # print('other_sum = ', other_sum)

    '''
        Step 3: Edge-weight normalization
    '''
    # First add a weight attribute to each edge.
    # weight_euv
    # print('all_edges : ', all_edges)
    # print('back_graph.adj : ', back_graph.adj)
    all_nodes = back_graph.nodes(data=True)
    all_nodes_list = list(back_graph.nodes(data=True))
    # print('all_nodes_list = ', all_nodes_list)
    # print('all_nodes = ', all_nodes)
    # print('all_nodes[powershell.exe_7784] = ', all_nodes['powershell.exe_7784'])
    # print('all_nodes[0] = ', list(all_nodes)[0][0])
    # print(back_graph.edges(0))
    # back_graph.edges(data=True)
    
    if not_use_lda:
        weight_euv = []
        for i in weights:
            # print(i)
            # w = i[0] + i[1] + i[2] + i[3]
            w = 0
            for j in i:
                w += j
            weight_euv.append(w)
    
    
    
    back_graph_adj = back_graph.adj
    all_edges = list(back_graph.edges(data=True, keys=True))
    
    # Add the previously calculated weight to each edge.
    for i in range(len(all_edges)):
        source, target, key, attr = all_edges[i]
        back_graph_adj[source][target][key]['weight'] = weight_euv[i]

    # print('back_graph.adj : ', back_graph.adj)
    # Sum each node's outgoing-edge weights and assign the result as the node weight.
    for i in range(len(all_nodes_list)):
        node_name = all_nodes_list[i][0]
        weight_sum = 0
        for j in back_graph_adj[node_name].keys():
            for k in back_graph_adj[node_name][j].keys():
                weight_sum += back_graph_adj[node_name][j][k]['weight']
        all_nodes[node_name]['weight'] = weight_sum
    # This should be all_nodes. Both all_nodes and all_nodes_list are references, so changing all_nodes also changes all_nodes_list.
    # print('back_graph.nodes = ', back_graph.nodes(data=True))
    # print('all_nodes_list = ', all_nodes_list)
    # Finally, calculate each edge's normalized weight.
    for i in range(len(all_nodes_list)):
        node_name = all_nodes_list[i][0]
        weight_sum = all_nodes_list[i][1]['weight']
        for j in back_graph_adj[node_name].keys():
            for k in back_graph_adj[node_name][j].keys():
                back_graph_adj[node_name][j][k]['weight'] = back_graph_adj[node_name][j][k]['weight'] / weight_sum


    # print(back_graph.edges(data=True))
    # if savefile:
    #     file_name = 'back_weight_graph_' + os.path.splitext(os.path.basename(filepath))[0]
    
    return back_graph


def impact_propagation(back_weight_graph, poi_event):
    """
    Propagate dependency impact.
    :param poi_event:
    :param back_weight_graph:
    :return: back_weight_graph, in which every node has a dependency-impact score.
    """
    back_weight_graph_adj = back_weight_graph.adj
    # all_edges = list(back_weight_graph.edges(data=True, keys=True))
    # print(back_weight_graph.adj)
    # print(all_edges)
    # source_node_name = 'powershell.exe_7784'
    # target_node_name = 'data/update.ps1'
    # detectionSize = 50781
    source_node_name = poi_event[0]
    target_node_name = poi_event[1]
    all_nodes = back_weight_graph.nodes(data=True)
    all_nodes[source_node_name]['score'] = 1
    all_nodes[target_node_name]['score'] = 1

    # all_edges = back_weight_graph.edges(data=True, keys=True)
    # print(all_edges)
    # print(all_nodes)

    # Calculate each node's score, skipping nodes without a score.
    # Create a queue.
    queue = Queue()
    queue.put(source_node_name)
    dead_list = [target_node_name]
    dead_set = set(dead_list)
    # dead_list = set([target_node_name])
    while not queue.empty():
        # Dequeue the front item.
        now = queue.get()
        # dead_list.add(now)
        # dead_list.append(now)
        dead_set.add(now)
        parent_nodes = list(back_weight_graph.predecessors(now))
        # Enqueue unvisited parent nodes.
        for i in parent_nodes:
            # if i not in dead_list:
            if i not in dead_set:
                queue.put(i)
        res = 0
        for child_name in back_weight_graph_adj[now].keys():
            # print('back_weight_graph_adj[name][child_name].keys() = ', back_weight_graph_adj[name][child_name].keys())
            for key in back_weight_graph_adj[now][child_name].keys():
                # print('key = ', key)
                # print(back_weight_graph_adj[name][child_name][key].keys())
                # print(back_weight_graph_adj[name][child_name][key]['weight'])
                # print(all_nodes[child_name]['score'])
                if 'score' in all_nodes[child_name].keys():
                    res += (back_weight_graph_adj[now][child_name][key]['weight'] * all_nodes[child_name]['score'])
        all_nodes[now]['score'] = res

    # print('after propagation all_nodes = ', all_nodes)

    # for node in all_nodes:
    # 	name, attr = node
    # 	all_nodes[name]['score'] = 1

    # print(list(back_weight_graph.nodes(data=True)))
    
    for node in all_nodes:
        name, attr = node
        if 'score' not in all_nodes[name].keys():
            all_nodes[name]['score'] = 1

    diff = sys.maxsize

    min_diff = 1e-13
    cycle_turn = 0
    while diff > min_diff and cycle_turn < 100:
        cycle_turn += 1
        diff = 0
        for node in all_nodes:
            name, attr = node
            if name == source_node_name or name == target_node_name:
                continue
            else:
                res = 0
                # print(back_weight_graph_adj[name].keys())
                for child_name in back_weight_graph_adj[name].keys():
                    # print('back_weight_graph_adj[name][child_name].keys() = ', back_weight_graph_adj[name][child_name].keys())
                    for key in back_weight_graph_adj[name][child_name].keys():
                        # print('key = ', key)
                        # print(back_weight_graph_adj[name][child_name][key].keys())
                        # print(back_weight_graph_adj[name][child_name][key]['weight'])
                        # print(all_nodes[child_name]['score'])
                        res += (back_weight_graph_adj[name][child_name][key]['weight'] * all_nodes[child_name]['score'])
                diff += (abs(attr['score'] - res))
                all_nodes[name]['score'] = res

    # print('after propagation all_nodes = ', all_nodes)
    return back_weight_graph


def entry_node_sort(back_weight_graph):
    """
    Rank entry nodes.
    :param back_weight_graph:
    :return: start_nodes, a list whose items contain [entry-node name, score].
    """
    start_nodes = []
    # Rank entry nodes.
    all_nodes = back_weight_graph.nodes(data=True)
    for node in all_nodes:
        name, attr = node
        parent_nodes = list(back_weight_graph.predecessors(name))
        if len(parent_nodes) == 0 or (len(parent_nodes) == 1 and name in parent_nodes):
            if len(start_nodes) == 0 or start_nodes[len(start_nodes) - 1][1] >= attr['score']:
                start_nodes.append([name, attr['score']])
            else:
                start_nodes1 = []
                i = 0
                while i < len(start_nodes) and start_nodes[i][1] >= attr['score']:
                    start_nodes1.append(start_nodes[i])
                    i += 1
                start_nodes1.append([name, attr['score']])
                i += 1
                while i < len(start_nodes):
                    start_nodes1.append(start_nodes[i])
                    i += 1
                start_nodes = start_nodes1

    # print(start_nodes)
    # for edge in all_edges:
    # 	print(edge[3]['weight'])
    # for i in start_nodes:
    # 	print(i[1])
    return start_nodes


def find_entry_node(graph):
    new_graph = nx.MultiDiGraph()
    nodes = graph.nodes(data=True)
    for node in nodes:
        # print(node)
        new_graph.add_node(node[0], name=node[0], type=node[1]['type'])
    edges = sorted(graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    entry_node_set = set()
    for e in edges:
        u, v, key, attr = e
        start_time = attr['start_time']
        type = attr['type']
        end_time = attr['end_time']
        data_amount = attr['data_amount']
        new_graph.add_edge(u, v, start_time=attr['start_time'], type=attr['type'], end_time=attr['end_time'],
                        data_amount=attr['data_amount'])
        if new_graph.in_degree(u) == 0:
            entry_node_set.add(u)
    return list(entry_node_set)


def get_sorted_entry_node(back_weight_graph):
    """
    Rank entry nodes.
    :param back_weight_graph:
    :return: start_nodes, a list whose items contain [entry-node name, score].
    """
    # Get entry nodes.
    entry_nodes = find_entry_node(back_weight_graph)
    start_nodes = []
    for node in entry_nodes:
        node_attr = back_weight_graph.nodes[node]
        start_nodes.append([node, node_attr['score']])
    # Rank entry nodes.
    start_nodes = sorted(start_nodes, key=lambda x: x[1], reverse=True)
    return start_nodes


def get_sorted_three_entry_node(back_weight_graph):
    """
    Rank entry nodes.
    :param back_weight_graph:
    :return: start_nodes, a list whose items contain [entry-node name, score].
    """
    # Get entry nodes.
    # entry_nodes = find_entry_node(back_weight_graph)
    start_nodes_file = []
    start_nodes_socket = []
    start_nodes_process = []
    
    for node in back_weight_graph.nodes(data=True):
        # node_attr = back_weight_graph.nodes[node]
        name, node_attr = node
        if node_attr['type'] == 'file':
            start_nodes_file.append([name, node_attr['score']])
        if node_attr['type'] == 'socket':
            start_nodes_socket.append([name, node_attr['score']])
        if node_attr['type'] == 'process':
            start_nodes_process.append([name, node_attr['score']])
        # start_nodes.append([node, node_attr['score']])
    # Rank entry nodes.
    # start_nodes = sorted(start_nodes, key=lambda x: x[1], reverse=True)
    start_nodes_file = sorted(start_nodes_file, key=lambda x: x[1], reverse=True)
    start_nodes_socket = sorted(start_nodes_socket, key=lambda x: x[1], reverse=True)
    start_nodes_process = sorted(start_nodes_process, key=lambda x: x[1], reverse=True)
    return start_nodes_file, start_nodes_socket, start_nodes_process


def get_start_nodes(start_nodes_file, start_nodes_socket, start_nodes_process, number):
    start_nodes = []
    for i in range(number):
        if i < len(start_nodes_file):
            start_nodes.append(start_nodes_file[i][0])
        if i < len(start_nodes_socket):
            start_nodes.append(start_nodes_socket[i][0])
        if i < len(start_nodes_process):
            start_nodes.append(start_nodes_process[i][0])
    return start_nodes

def get_start_nodes_with_score(start_nodes_file, start_nodes_socket, start_nodes_process, number):
    start_nodes = []
    for i in range(number):
        if i < len(start_nodes_file):
            start_nodes.append(start_nodes_file[i])
        if i < len(start_nodes_socket):
            start_nodes.append(start_nodes_socket[i])
        if i < len(start_nodes_process):
            start_nodes.append(start_nodes_process[i])
    return start_nodes
