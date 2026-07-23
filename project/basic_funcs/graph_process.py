#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import gzip
import os
import pickle

import networkx as nx

def read_graph(file_path):
    """Read a pickled NetworkX graph, optionally compressed with gzip."""
    opener = gzip.open if str(file_path).endswith(".gz") else open
    with opener(file_path, "rb") as graph_file:
        return pickle.load(graph_file)


def save_graph(G, file_path, file_name):
    """Save a graph.

    :param _type_ G: _description_
    :param _type_ file_path: Storage path.
    :param _type_ file_name: File name without an extension.
    :return _type_: _description_
    """
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    output_path = os.path.join(file_path, file_name + ".gz")
    with gzip.open(output_path, "wb") as graph_file:
        pickle.dump(G, graph_file, protocol=pickle.HIGHEST_PROTOCOL)


"""
    Process attack events.
"""
def get_large_case_attack_events(file_name, groundTruthEdges, large_case_names):
    """Get attack events for a large case.

    :param _type_ file_name: _description_
    :param _type_ groundTruthEdges: _description_
    :param _type_ large_case_names: _description_
    :return _type_: _description_
    """
    ls = []
    for name in large_case_names[file_name]:
        for e in groundTruthEdges[name]:
            ls.append(e)
    return ls


def find_groundTruth_events(groundTruth_events, G):
    """
    Find event details corresponding to the ground-truth events.
    :param groundTruth_events: Ground-truth events in the following format:
    [('process_7620', 'data/browser/add-on/example'),]
    :param G: Graph containing all events.
    :return: List of attack events: [(u,v,key,attr), ...].
    """
    attack_events = []
    adj = G.adj
    # print(type(adj))
    # print(adj)
    not_in_G = set()
    for e in groundTruth_events:
        u = e[0]
        v = e[1]
        if u in adj.keys():
            if v in adj[u].keys():
                events = G.adj[u][v]
                for key in events.keys():
                    tuple_e = (u, v, key, events[key])
                    attack_events.append(tuple_e)
            else:
                not_in_G.add(v)
        else:
            not_in_G.add(u)
    return attack_events, not_in_G


def remove_attack_events(G, attack_events):
    """
    Remove attack events from the graph of all events.
    :param G:
    :param attack_events: [e1, e2, ...]  e1: (u, v, key, attr)
    :return: Graph after removal.
    """
    for e in attack_events:
        u, v, key, attr = e
        if G.has_edge(u, v, key=key):
            # print("remove edge :({}, {}, {})".format(u, v, key))
            G.remove_edge(u, v, key=key)
    return G


"""
    Compress a graph.
"""


def SementicCompress(G):
    """
    Suspicious-semantic compression.
    :param G:
    :return: Compressed graph.
    """
    socketConection = {"recvfrom", "recvmsg", "sendto", "write", "read", "writev", "readv"}
    writeConection = {"write", "writev"}
    readConection = {"read", "readv"}
    processConection = {"execve", "fork", "clone"}
    edges = sorted(G.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    SementicSet = set()
    event_set = set()
    for e in edges:
        # print(G.nodes[e[0]])
        sub, obj, subT, objT = e[0], e[1], G.nodes[e[0]]['type'], G.nodes[e[1]]['type']
        # print(subT)
        # print(objT)
        event_set.add(subT)
        event_set.add(objT)
        if e[3]['type'] in socketConection:  # S -> P  / P -> S
            if subT == "socket":
                SementicSet.add(sub)
                SementicSet.add(obj)
                continue
            elif objT == "socket":
                SementicSet.add(sub)
                SementicSet.add(obj)
                continue
        if e[3]['type'] in writeConection:  # P -> F
            if sub in SementicSet and G.nodes[e[1]]['type'] == 'file':
                SementicSet.add(obj)
                continue
        if e[3]['type'] in readConection:  # F -> P
            if sub in SementicSet and G.nodes[e[0]]['type'] == 'file':
                SementicSet.add(obj)
                continue
        if e[3]['type'] in processConection:  # P -> P
            if sub in SementicSet:
                SementicSet.add(obj)
                continue
    # print(event_set)
    # print('len(SementicSet) = ', len(SementicSet))
    nodes = G.nodes()
    removing_nodes = set()
    # print(nodes)
    for node in nodes:
        if node not in SementicSet:
            # G.remove_node(node)
            removing_nodes.add(node)
    for node in removing_nodes:
        G.remove_node(node)
    return G


def remove_special_filenode(G):
    # specialFile = ['/dev/null', '/dev/zero', '/dev/random', '/dev/urandom', '/dev/full', '/dev/tty', '/dev/mem']
    nodeDel = []
    for node in G.nodes():
        if G.nodes[node]['type'] == 'file' and (node.startswith('/dev') or node.startswith('/proc') or \
    node.startswith('/mnt') or node.startswith('/usr') or \
    node.startswith('/root') or node.startswith('/etc') or \
    node.startswith('/run') or node.startswith('/lib') or \
    node.startswith('/var') or node.startswith('/sys')):
            nodeDel.append(node)
    G.remove_nodes_from(nodeDel)
    return G


def remove_isolated_point(G):
    """
    Remove read-only files.
    :param G:
    :return: Graph after removal.
    """
    nodeDel = []
    for node in G.nodes():
        if G.nodes[node]['type'] == 'file' and list(G.predecessors(node)) == []:
            nodeDel.append(node)
    G.remove_nodes_from(nodeDel)
    return G


def ls_sort(ls):
    if len(ls) < 2:
        return ls
    # Bubble sort.
    flag = False
    for i in range(len(ls) - 1):
        for j in range(0, len(ls) - i - 1):
            keys1 = list(ls[j].keys())
            print(keys1)
            print(type(keys1))
            keys2 = list(ls[j + 1].keys())
            if len(keys1) != 1 or len(keys2)  != 1:
                print('ERROR : ********len(keys1) != 1 or len(keys2)  != 1************')
                return None
            key1 = keys1[0]
            key2 = keys2[0]
            print(key1, ', ', key2)
            if ls[j][key1]['start_time'] > ls[j + 1][key2]['start_time']:
                flag = True
                temp = ls[j + 1]
                ls[j + 1] = ls[j]
                ls[j] = temp
        if not flag:
            break
        else :
            flag = False
    return ls


def remove_redundant_edge_small(G, max_time):
    """
    Remove events within a given time range.
        ****This creates a new graph directly and may need optimization.****
    :param G:
    :param max_time:
    :return:
    """
    # Remove read-only file nodes first.
    # G = remove_isolated_point(G)
    edges = sorted(G.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    G1 = nx.MultiDiGraph()
    nodes = G.nodes(data=True)
    for node in nodes:
        # print(node)
        G1.add_node(node[0], name=node[0], type=node[1]['type'])
    # 1. Remove redundant edges occurring within 10 seconds.
    for e in edges:
        u, v, key, attr = e
        start_time = attr['start_time']
        type = attr['type']
        end_time = attr['end_time']
        data_amount = attr['data_amount']
        out_edges = G1.edges(u, keys=True, data=True)
        adj = G1.adj
        flag = True
        if u in adj.keys() and v in adj[u].keys() and len(adj[u][v]) > 0:
            # If u and v have one or more edges, compare their types and timestamps.
            for key in adj[u][v]:
                type1 = adj[u][v][key]['type']
                time = adj[u][v][key]['start_time']
                # if type1 == type and abs(int(time) - int(start_time)) < max_time:
                if type1 == type and abs(float(time) - float(start_time)) < max_time:
                    # An edge with the same type and a time difference under 10 seconds does not need to be added.
                    # print(e)
                    flag = False
                    break
        if flag:
            G1.add_edge(u, v, start_time=attr['start_time'], type=attr['type'], end_time=attr['end_time'],
                        data_amount=attr['data_amount'])
    G1 = remove_isolated_point(G1)
    return G1


def remove_redundant_edge_large(G, max_time):
    """
    Remove events within a given time range.
        Remove events directly from the original graph to avoid running out of memory.
    :param G:
    :param max_time:
    :return:
    """
    # Remove read-only file nodes first.
    # G = remove_isolated_point(G)
    edges = sorted(G.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    
    # 1. Remove redundant edges occurring within 10 seconds.
    for e in edges:
        u, v, key, attr = e
        if not G.has_edge(u, u, key): continue
        
        if len(G[u][v]) <= 1: continue

        can_remove_events = [(u, v, k, value) for k, value in G[u][v].items() if value['type'] == e[3]['type'] and value['start_time'] != e[3]['start_time'] and abs(float(value['start_time']) - float(e[3]['start_time'])) < max_time] 
        for e1 in can_remove_events:
            u1, v1, key1, attr1 = e1
            # Retain the current event and remove the others.
            if key1 == key and u == u1 and v == v1: continue
            G.remove_edge(u1, v1, key=key1)
    G = remove_isolated_point(G)
    return G


def remove_redundant_edges(G, max_time):
    """
    Remove events within a given time range.
        Remove events directly from the original graph to avoid running out of memory.
    :param G:
    :param max_time:
    :return:
    """
    # Remove read-only file nodes first.
    # G = remove_isolated_point(G)
    edges = sorted(G.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    
    # 1. Remove redundant edges occurring within 10 seconds.
    for e in edges:
        u, v, key, attr = e
        if not G.has_edge(u, v, key): continue
        
        if len(G[u][v]) <= 1: continue

        can_remove_events = [(u, v, k, value) for k, value in G[u][v].items() if value['type'] == e[3]['type'] and value['start_time'] != e[3]['start_time'] and abs(float(value['start_time']) - float(e[3]['start_time'])) < max_time] 
        for e1 in can_remove_events:
            u1, v1, key1, attr1 = e1
            # Retain the current event and remove the others.
            if key1 == key and u == u1 and v == v1: continue
            G.remove_edge(u1, v1, key=key1)
    return G

def compress_graph(G, max_time):
    """Compress a graph using suspicious-semantic and redundant-edge compression.

    :param _type_ G: _description_
    :return _type_: _description_
    """
    
    # max_time = 10000
    G = remove_redundant_edges(G, max_time)
    # G = SementicCompress(G)
    G = remove_isolated_point(G)
    return G


def find_back_graph(G, poi_event, isEqual=False):
    """Get a backward dependency graph based on Poi_event.
    :param _type_ G: _description_
    :param _type_ poi_event: _description_
    :param bool isEqual: Whether time comparisons include equality; defaults to False.
    :return _type_: _description_
    """
    p = tuple(poi_event)
    edgesL = set([p])
    tempL = [p]
    while tempL:
        e = tempL.pop()
        for inEdge in G.in_edges(e[0], keys=True):
            if inEdge in edgesL:continue
            if isEqual:
                if inEdge not in edgesL and G[inEdge[0]][inEdge[1]][inEdge[2]]['start_time'] <= G[e[0]][e[1]][e[2]]['start_time']:
                    tempL.append(inEdge)
                    edgesL.add(inEdge)
            else :
                if inEdge not in edgesL and G[inEdge[0]][inEdge[1]][inEdge[2]]['start_time'] < G[e[0]][e[1]][e[2]]['start_time']:
                    tempL.append(inEdge)
                    edgesL.add(inEdge)
        # e = tempL.pop()
        # if e in edgesL:continue
        # edgesL.append(e)
        # # visitedL.append(e)
        # for inEdge in G.in_edges(e[0], keys=True):
        #     if inEdge not in edgesL and G[inEdge[0]][inEdge[1]][inEdge[2]]['start_time'] < G[e[0]][e[1]][e[2]]['start_time']:
        #         tempL.append(inEdge)
        # nodesL.append(e[0])
    edgesL = list(edgesL)
    subGraph = G.edge_subgraph(edgesL).copy()       
    return subGraph

def forward_analysis(G, entry_nodes, num_of_nodes):
    """Get a forward dependency graph based on entry points and their count.

    :param _type_ G: _description_
    :param _type_ entry_nodes: _description_
    :param _type_ num_of_nodes: _description_
    :return _type_: _description_
    """
    dead_edges = set()
    # edges = []
    for i in range(num_of_nodes):
        # Iterate over the highest-ranked nodes.
        node_name = entry_nodes[i][0]
        # Get the node's outgoing edges.
        out_edges = G.out_edges(node_name, keys=True)
        tempL = []
        for e in out_edges:
            if e not in dead_edges:
                # edges.append(e)
                tempL.append(e)
            dead_edges.add(e)
        while tempL:
            e = tempL.pop()
            for inEdge in G.out_edges(e[0], keys=True):
                if inEdge in dead_edges:continue
                if inEdge not in dead_edges and G[inEdge[0]][inEdge[1]][inEdge[2]]['end_time'] >= G[e[0]][e[1]][e[2]]['start_time']:
                    tempL.append(inEdge)
                    # edges.append(inEdge)
                    dead_edges.add(inEdge)
        # e = tempL.pop()
        # if e in edgesL:continue
        # edgesL.append(e)
        # # visitedL.append(e)
        # for inEdge in G.in_edges(e[0], keys=True):
        #     if inEdge not in edgesL and G[inEdge[0]][inEdge[1]][inEdge[2]]['start_time'] < G[e[0]][e[1]][e[2]]['start_time']:
        #         tempL.append(inEdge)
        # nodesL.append(e[0])
    dead_edges = list(dead_edges)
    subGraph = G.edge_subgraph(dead_edges).copy()
    return subGraph


def forward_analysis_new(G, entry_nodes, num_of_nodes):
    """Get a forward dependency graph based on entry points and their count.

    :param _type_ G: _description_
    :param _type_ entry_nodes: _description_
    :param _type_ num_of_nodes: _description_
    :return _type_: _description_
    """
    dead_edges = set()
    for i in range(num_of_nodes):
        node_name = entry_nodes[i][0]
        out_edges = G.out_edges(node_name, keys=True)
        tempL = []
        # Add edges directly reachable from the current node to dead_edges.
        for e in out_edges:
            if e not in dead_edges:
                tempL.append(e)
            dead_edges.add(e)
        while tempL:
            # Use the tempL queue to obtain edges reachable by its successor nodes.
            e = tempL.pop()
            for next_edges in G.out_edges(e[1], keys=True):
                if next_edges in dead_edges:continue
                if next_edges not in dead_edges and G[next_edges[0]][next_edges[1]][next_edges[2]]['end_time'] >= G[e[0]][e[1]][e[2]]['start_time']:
                    tempL.append(next_edges)
                    # edges.append(inEdge)
                    dead_edges.add(next_edges)
    dead_edges = list(dead_edges)
    # print(f'len of dead_edges {len(dead_edges)}')
    # print(dead_edges)
    # print()
    # print()
    subGraph = G.edge_subgraph(dead_edges).copy()
    return subGraph


def is_gt_in_graph(graph, gt_events):
    """Test whether the corresponding edges exist in the graph.

    :param networkx.MultiDiGraph graph: Graph.
    :param list gt_events: Event list: [(u1, v1), (u2, v2), ...].
    :return list not_in_origin: Events not present in the graph.
    :return int: TP (u,v or v,u), TP1 (strictly ordered as u,v), TP2 (strictly ordered as v,u), and FN.
    """
    not_in_origin = []
    TP, TP1, TP2, FN = 0, 0, 0, 0
    for ce in gt_events:
        if graph.has_edge(ce[0], ce[1]):
            TP += 1
        if graph.has_edge(ce[1], ce[0]):
            TP1 += 1
        if graph.has_edge(ce[0], ce[1]) or graph.has_edge(ce[1], ce[0]):
            TP2 += 1
        else: 
            FN += 1
            not_in_origin.append(ce)
    return not_in_origin, TP, TP1, TP2, FN


def add_edges_graph(origin_graph, need_add_edges, graph):
    """Add edges.
    Usage:
    1. Use is_gt_in_graph to find not_in_origin, the list of events absent from the graph.
    2. Use find_need_add_edges to find the edges that must be added.
    3. Use add_edges_graph to add the edges.
    
    :param _type_ origin_graph: _description_
    :param _type_ need_add_edges: _description_
    :param _type_ graph: _description_
    :return _type_ graph: _description_
    """
    for e in need_add_edges:
        u, v, key = e
        type = origin_graph.adj[u][v][key]['type']
        data_amount = origin_graph.adj[u][v][key]['data_amount']
        start_time = origin_graph.adj[u][v][key]['start_time']
        end_time = origin_graph.adj[u][v][key]['end_time']
        
        # if 'type' not in back_graph.nodes[node].keys():
        if 'xx.xx.xx.xx->xx.xx.xx.xx' == u: # and 'type' not in graph.nodes():
            graph.add_node(u, type='socket', name=u)
        else:
            if u not in graph.nodes() and u in origin_graph.nodes():
                type1 = origin_graph.nodes[u]['type']
                graph.add_node(u, type=type1, name=u)
            # else:
            #     print(f'{u} not in origin_graph.nodes()')
        # if v not in back_graph.nodes():
        if 'xx.xx.xx.xx->xx.xx.xx.xx' == v:# and 'type' not in graph.nodes[v].keys():
            graph.add_node(v, type='socket', name=v)
        else:
            if v not in graph.nodes() and v in origin_graph.nodes():
                type1 = origin_graph.nodes[v]['type']
                graph.add_node(v, type=type1, name=v)
            # elif v not in back_graph.nodes() and v in origin_graph.nodes():
            #     print(f'{v} not in origin_graph.nodes()')
        graph.add_edge(u, v, type=type, data_amount=data_amount, start_time=start_time, end_time=end_time)
    return graph


def find_need_add_edges(not_in_origin, origin_graph):
    """Find edges that need to be added.

    :param _type_ not_in_origin: _description_
    :param _type_ origin_graph: _description_
    :return _type_: _description_
    """
    need_add_edges = set()
    for e in not_in_origin:
        u, v = e
        if origin_graph.has_edge(u, v):
            edge_data = origin_graph.get_edge_data(u, v)
            # if len(edge_data.keys()) < 10:
            #     print(f'{u}, {v}, {edge_data}')
            # else :
            #     print(f'len(edge_data.keys()) = {len(edge_data.keys())}')
            for key in edge_data.keys():
                need_add_edges.add((u, v, key))
    return need_add_edges


def add_edges(poi_name, need_add_graph, origin_graph, gt_events, max_time=10000, need_compress=True):
    """Create a new graph by adding all missing edges to a graph containing all ground-truth events.

    :param _type_ poi_name: _description_
    :param _type_ need_add_graph: _description_
    :param _type_ origin_graph: _description_
    :param _type_ gt_events: _description_
    :return _type_: _description_
    """
    not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(need_add_graph, gt_events)
    need_add_edges = find_need_add_edges(not_in_origin, origin_graph)
    graph = add_edges_graph(origin_graph, need_add_edges, need_add_graph)
    if need_compress: graph = compress_graph(graph, max_time)
    return graph


def get_graph_fn_fp(graph, gt_events_set):
    """Calculate forward-graph results.

    :param _type_ graph: Events in the graph are predicted as anomalous; events outside it are predicted as normal.
    :param set gt_events_set: Set of ground-truth events.
    :return int tp: In the ground truth and in the graph (actually anomalous and predicted anomalous).
    :return int fn: In the ground truth but not in the graph (actually anomalous but predicted normal).
    :return int fp: Not in the ground truth but in the graph (actually normal but predicted anomalous).
    tn: Actually normal and predicted normal. This does not appear to be calculable here and should be calculated during processing.
    
    :return int tn: Neither in the ground truth nor in the graph.
    """
    fn, fp, tp = 0, 0, 0
    # Calculate FP and TN.
    for e in graph.edges():
        u, v = e[0], e[1]
        if (u, v) not in gt_events_set: # Not in the ground truth but in the graph.
            fp += 1
        else: # In both the ground truth and the graph.
            tp += 1
    for e in gt_events_set:
        u, v = e[0], e[1]
        if not graph.has_edge(u, v): # In the ground truth but not in the graph.
            fn += 1
    return fn, fp, tp


def print_graph_info(graph, poi_name, gt_events=None):
    """Get graph information: edge and node counts, TP, FP, and FN.

    :param _type_ graph: _description_
    :param _type_ poi_name: _description_
    :param _type_ gt_events: _description_
    """
    len_nodes1 = graph.number_of_nodes()
    len_edges1 = graph.number_of_edges()
    if gt_events is not None:
        not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(graph, gt_events)
        print(f'{poi_name}, {len_nodes1}, {len_edges1}, {TP}, {FN}, {len_edges1-TP}')
    else:
        print(f'{poi_name}, {len_nodes1}, {len_edges1}')
    
    
