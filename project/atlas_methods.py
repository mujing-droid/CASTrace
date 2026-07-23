#!/usr/bin/env python3
# -*- encoding: utf-8 -*-


'''
ATLAS steps:
Data preparation: backward dependency graph, key edges, and key nodes
0. Optimize the dependency graph
1. Build sequences (attack and non-attack sequences)
2. Tokenize sequences
3. Sample
4. Embed
5. Train the model (completed)
'''


import networkx as nx
from itertools import combinations


def is_one_edge(graph, nodes, now_node, is_next_node=True):
    static_event = None
    if len(nodes) >= 1:
        for node in nodes:
            if is_next_node:
                if len(graph.adj[now_node][node].keys()) != 1:
                    return False
                if static_event is None:
                    static_event = graph.adj[now_node][node][0]['type']
                elif static_event != graph.adj[now_node][node][0]['type']:
                    return False
            if not is_next_node:
                if len(graph.adj[node][now_node].keys()) != 1:    
                    return False
                if static_event is None:
                    static_event = graph.adj[node][now_node][0]['type']
                elif static_event != graph.adj[node][now_node][0]['type']:
                    return False
        return True    
    return False


def remove_duplicate_edge(graph):
    """ATLAS data-compression method: remove duplicate edges.
    1. For edges between two nodes, retain only the earliest edge for each event.
    :param _type_ graph: _description_
    """
    edges = sorted(graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    # Retain only the earliest edge for each event.
    nodes_event_set = {}
    edges_set = set()
    for e in edges:
        u, v, key, attr = e
        event_type = attr['type']
        if u not in nodes_event_set.keys():
            nodes_event_set[u] = set([event_type])
            edges_set.add((u, v, key))
        elif event_type not in nodes_event_set[u]:
            nodes_event_set[u].add(event_type)
            edges_set.add((u, v, key))
    edges_list = list(edges_set)
    G = graph.edge_subgraph(edges_list).copy()
    return G


def merge_node(G):
    """ATLAS data-compression method: merge nodes.
    2. Merge same-type incoming or outgoing edges of a node into one edge, and merge the nodes.
    :param _type_ G: _description_
    """
    # 2. Merge same-type incoming or outgoing edges of a node into one edge, and merge the nodes.
    # The ATLAS source is extensive and difficult to follow. Broadly, it only merges file nodes whose predecessor and successor nodes match.
    # First, find file nodes whose predecessor and successor each have only one edge, or that have no predecessor/successor.
    # Then handle three cases:
    # 1. The node has both a predecessor and a successor:
        # Find its predecessor and check whether all successor edges of that predecessor have the same type. Then check whether all predecessor edges of its successor have the same type. Merge them if both conditions hold.
    # 2. The node has a predecessor but no successor: merge if all successor edges of its predecessor have the same type.
    # 3. The node has no predecessor but has a successor: merge if all predecessor edges of its successor have the same type.
    
    file_nodes = set()
    # Find eligible file nodes.
    for node in G.nodes(data=True):
        # The node format here lacks a name: ('bash_8292', {'pid': '8292', 'type': 'process'}).
        # if 'name' not in node[1].keys():
        #     print(node)
        #     continue
        # print(node)
        node_name = node[0]
        flag_pre = True
        flag_suc = True
        try:
            pre_nodes = list(G.predecessors(node_name))
            # suc_nodes = list(G.successors(node_name))
        except Exception as e:
            # print(e)
            flag_pre = False
            continue
        try:
            # pre_nodes = list(G.predecessors(node_name))
            suc_nodes = list(G.successors(node_name))
        except Exception as e:
            # print(e)
            flag_suc = False
            continue
        # print(type(pre_nodes))
        # print(type(suc_nodes))
        # print(list(pre_nodes))
        if len(pre_nodes) == 0 and len(suc_nodes) == 0:
            G.remove_node(node_name)
            continue
        if len(pre_nodes) == 0 or len(suc_nodes) == 0:
            file_nodes.add(node_name)
        elif len(pre_nodes) == 1 and len(suc_nodes) == 1 and pre_nodes == suc_nodes:
            file_nodes.add(node_name)
    if len(file_nodes) == 0:
        print("没有符合条件的文件节点")
        return None
    # need_merge_nodes = {1: [], 2: [], 3: []}
    # for file_node in file_nodes:
    #     # Iterate over eligible file nodes and determine which of the three cases applies.
    #     pre_nodes = G.predecessors(file_nodes)
    #     suc_nodes = G.successors(file_nodes)
        
    #     if len(pre_nodes) == 1 and len(suc_nodes) == 1:
    #         # Case 1.
    #         # Obtain pre_suc_nodes, all successors of predecessor p of node q.
    #         # Find the file nodes among these successors and record them in file_nodes.
    #         # Find edges from the successor nodes to the file nodes. If their types match, proceed to find all edges of that type.
    #         # Start from the file node.
    #         pre_node = pre_nodes[0]
    #         suc_node = suc_nodes[0]
            
    #         pre_event_type = G.adj[pre_node][file_node][0]['type']
    #         suc_event_type = G.adj[file_node][suc_node][0]['type']
            
    #         pre_suc_nodes = G.predecessors(pre_node)
    #         if len(pre_suc_nodes) > 1:
    #             # More than one successor of p means that nodes other than the current file_node exist.
    #             pre_suc_file_nodes = []
    #             for node1 in pre_suc_nodes:
    #                 if node1 == file_node:
    #                     # Exclude the current file_node for convenience.
    #                     continue
    #                 if G.nodes(node1)['type'] == 'file':
    #                     # Find file nodes among the successors of file_node's predecessor.
    #                     pre_suc_file_nodes.append(node1)
    #             # At least one file node is required for such a node to exist.
    #             if len(pre_suc_file_nodes) >= 1:
    #                 # Find file nodes whose event type matches the current node; they may be mergeable if their successor events also match.
    #                 same_pre_nodes = []
    #                 for node1 in pre_suc_file_nodes:
    #                     if G.adj[pre_node][node1][0]['type'] == pre_event_type:
    #                         same_pre_nodes.append(node1)
    #                 # same_pre_nodes records the nodes described above; at least one is required.
    #                 if len(same_pre_nodes) >= 1:
    #                     # Find successors of nodes in same_pre_nodes whose event type matches file_node.
    #                     for node1 in same_pre_nodes:
    #                         node1_suc_nodes = G.successors(node1)
    #                         if len(node1_suc_nodes) == 1 and node1_suc_nodes[0] == suc_node and G.adj[node1][suc_node][0]['type'] == suc_event_type:
    #                             # The node and file_node have the same successor and event type.
    return file_nodes
    


def atlas_compress(graph):
    """ATLAS data-compression method.
    1. For edges between two nodes, retain only the earliest edge for each event.
    2. Merge same-type incoming or outgoing edges of a node into one edge, and merge the nodes.
    :param _type_ graph: _description_
    """
    compressed_graph = remove_duplicate_edge(graph)
    # graph2 = merge_node(compressed_graph)
    return compressed_graph


def find_neighbor_graph(graph, nodes):
    """Get a neighborhood graph.

    :param nx.MultiDiGraph graph: _description_
    :param list nodes: List of node-name strings.
    """
    edges_set = set()
    for node in nodes:
        for edge in graph.in_edges(node, keys=True, data=True):
            u, v, key, attr = edge
            edges_set.add((u, v, key))
        for edge in graph.out_edges(node, keys=True, data=True):
            u, v, key, attr = edge
            edges_set.add((u, v, key))
    neighbor_graph = graph.edge_subgraph(edges_set).copy()
    return neighbor_graph


def get_combinations(nodes_list, max_len=None):
    ls = []
    len_list = len(nodes_list)
    if max_len is not None:
        len_list = max_len
    for i in range(2, len_list + 1):
        ls1 = combinations(nodes_list, i)
        for j in ls1:
            ls.append(j)
    return ls


def get_combinations_max_len(nodes_list, max_len):
    ls = []
    max_len_comb = len(nodes_list)
    if max_len_comb > max_len:
        max_len_comb = max_len
    for i in range(2, max_len_comb + 1):
        ls1 = combinations(nodes_list, i)
        for j in ls1:
            ls.append(j)
    return ls


dict1 = {
    "system_process": set([
        "systemd", "cron", "sshd", "pg_isready_22727", "pg_isready_8172", "apparmor_parser_22734", 
        "apparmor_parser_22732", "apparmor_parser_22726", "apparmor_parser_22768", "apparmor_parser_22769", 
        "docker-runc", "apt-get", "apt-key", "man-db", "update-motd-reb", "apt.systemd.dai", "unshadow", 
        "update-motd-fsc", "runc:[1:child]"
    ]),
    "program_process": set([
        "python", "python3", "bash", "sh", "wget", "curl", "ssh", "scp", "top", "which", "cat", "grep", 
        "sed", "cut", "echo", "ls", "mv", "cp", "ping", "unzip", "bzip2", "solc", "solc-v0.5.11", 
        "powershell.exe", "john", "mesg", "dumpe2fs", "release-upgrade", "gpg", "gpgv", "gdbus"
    ]),
    "user_process": set([
        "firefox", "fluxbox", "entrypoint.sh", "setup.sh", "run.sh", "00-header", "10-help-text", 
        "50-motd-news", "90-updates-avai", "97-overlayroot"
    ]),
    "library_process": [] 
}
def change_node(type, node):
    node = node.lower().strip()
    if type == "file":
        if 'sys' in node:
            return 'system_file'
        if 'lib' in node:
            return 'lib_file'
        if 'proc' in node:
            return 'proc_file'
        if 'tmp' in node:
            return 'temp_file'
        if 'usr' in node:
            return 'user_file'
        return 'other_file'
    if type == "process":
        for key, value in dict1.items():
            for i in value:
                if i in node:
                    return key
        # if node in dict1["system_process"]:
        #     return 'system_process'
        # if node in dict1["program_process"]:
        #     return 'programs_process'
        # if node in dict1["user_process"]:
        #     return 'user_process'
        return 'lib_process'
    return 'ip_address'


def node_to_label(graph):
    """Map node types directly to labels.

    :param _type_ graph: _description_
    :return dict node_to_labels_dict: {node: label, ...}
    """
    node_to_labels_dict = {}
    for node in graph.nodes(data=True):
        lable = change_node(node[1]['type'], node[0])
        node_to_labels_dict[node[0]] = lable
    return node_to_labels_dict

def get_sequence(edges, graph):
    s = ''
    for edge in edges:
        u, v, key, attr = edge
        u_type = graph.nodes[u]['type']
        v_type = graph.nodes[v]['type']
        u_new_word = change_node(u_type, u)
        v_new_word = change_node(v_type, v)
        s = s + " " + u_new_word + " " + attr['type'] + " " + v_new_word
    return s


def get_sequence_nonattack(edges, graph):
    s = ''
    for edge in edges:
        u, v, key, type, time = edge
        u_type = graph.nodes[u]['type']
        v_type = graph.nodes[v]['type']
        u_new_word = change_node(u_type, u)
        v_new_word = change_node(v_type, v)
        s = s + " " + u_new_word + " " + type + " " + v_new_word
    return s

def get_sequence_using_dict(edges, node_labels_dict):
    s = ''
    for edge in edges:
        u, v, key, attr = edge
        u_new_word = node_labels_dict[u]
        v_new_word = node_labels_dict[v]
        s = s + " " + u_new_word + " " + attr['type'] + " " + v_new_word
    return s


def get_sequence_nonattack_using_dict(edges, node_labels_dict):
    s = ''
    for edge in edges:
        u, v, key, type, time = edge
        u_new_word = node_labels_dict[u]
        v_new_word = node_labels_dict[v]
        s = s + " " + u_new_word + " " + type + " " + v_new_word
    return s

def get_attack_sequence(graph, attack_nodes_list):
    """Get attack sequences.

    :param _type_ graph: _description_
    :param _type_ attack_nodes_list: _description_
    """
    seqs_set = set()
    # attack_nodes_list = get_combinations(attack_nodes)
    comb_nodes_edges_dict = {}
    for comb_nodes in attack_nodes_list:
        neighbor_graph = find_neighbor_graph(graph, comb_nodes)
        # Get events.
        edges = sorted(neighbor_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
        # Extract and map sequences.
        s = get_sequence(edges, neighbor_graph)
        edges1 = []
        for e in edges:
            u, v, key, attr = e
            edges1.append((u, v, key, attr['type'], attr['start_time']))
        comb_nodes_edges_dict[comb_nodes] = edges1
        seqs_set.add(s)
    # ls = [i for i in seqs_set]
    return seqs_set, comb_nodes_edges_dict


def get_attack_sequence_using_dict(graph, attack_nodes_list, node_labels_dict):
    """Get attack sequences.

    :param _type_ graph: _description_
    :param _type_ attack_nodes_list: _description_
    :return set seqs_set: Set of sequences.
    :return dict comb_nodes_edges_dict: Dictionary mapping combined nodes to edge lists.
    :return dict comb_nodes_seqs_dict: Dictionary mapping combined nodes to sequences.
    """
    seqs_set = set()
    # attack_nodes_list = get_combinations(attack_nodes)
    comb_nodes_edges_dict = {}
    comb_nodes_seqs_dict = {}
    for comb_nodes in attack_nodes_list:
        neighbor_graph = find_neighbor_graph(graph, comb_nodes)
        # Get events.
        edges = sorted(neighbor_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
        # Extract and map sequences.
        s = get_sequence_using_dict(edges, node_labels_dict)
        edges1 = []
        for e in edges:
            u, v, key, attr = e
            edges1.append((u, v, key, attr['type'], attr['start_time']))
        comb_nodes_edges_dict[comb_nodes] = edges1
        seqs_set.add(s)
        comb_nodes_seqs_dict[str(comb_nodes)] = s
    # ls = [i for i in seqs_set]
    return seqs_set, comb_nodes_edges_dict, comb_nodes_seqs_dict


def get_nonattack_sequence(graph, nonattack_nodes, attack_nodes_list, set_attack_seqs):
    """Get non-attack sequences.

    :param _type_ graph: _description_
    :param _type_ nonattack_nodes: _description_
    """
    seqs_set = set()
    for comb_nodes in attack_nodes_list:
        ls = [i for i in comb_nodes]
        set1 = set()
        for node in nonattack_nodes:
            if node not in set1:
                ls.append(node)
                neighbor_graph = find_neighbor_graph(graph, ls)
                # Get events.
                edges = sorted(neighbor_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
                # Extract and map sequences.
                s = get_sequence(edges, neighbor_graph)
                if s not in set_attack_seqs:
                    seqs_set.add(s)
    # ls = [i for i in seqs_set]
    return seqs_set


def get_nonattack_sequence_with_dict(graph, nonattack_nodes, comb_nodes_edges_dict, attack_nodes_list, set_attack_seqs):
    """Get non-attack sequences.

    :param _type_ graph: _description_
    :param _type_ nonattack_nodes: _description_
    """
    seqs_set = set()
    for comb_nodes in attack_nodes_list:
        # ls = [i for i in comb_nodes]
        set1 = set(comb_nodes)
        
        
        for node in nonattack_nodes:
            if node not in set1:
                
                # Extract and map sequences.
                edges = comb_nodes_edges_dict[comb_nodes]
                # Next, find edges to add: incoming and outgoing edges of node whose other endpoint is in comb_nodes.
                in_edges = graph.in_edges(node, keys=True, data=True)
                out_edges = graph.out_edges(node, keys=True, data=True)
                flag1 = False
                flag2 = False
                for edge in in_edges:
                    u, v, key, attr = edge
                    if u in comb_nodes:
                        edges.append((u, v, key, attr['type'], attr['start_time']))
                        flag1 = True
                for edge in out_edges:
                    u, v, key, attr = edge
                    if v in comb_nodes:
                        edges.append((u, v, key, attr['type'], attr['start_time']))
                        flag2 = True
                if flag1 or flag2:    
                    edges = sorted(edges, key=lambda t: t[4])
                    s = get_sequence_nonattack(edges, graph)
                    if s not in set_attack_seqs:
                        seqs_set.add(s)
    # ls = [i for i in seqs_set]
    return seqs_set


def get_nonattack_sequence_with_label_dict(graph, nonattack_nodes, comb_nodes_edges_dict, attack_nodes_list, set_attack_seqs, node_labels_dict):
    """Get non-attack sequences.

    :param _type_ graph: _description_
    :param _type_ nonattack_nodes: _description_
    :param dict comb_nodes_edges_dict: Mapping between combined attack-sequence nodes and edges.
    :param list attack_nodes_list: List of combined attack nodes.
    :param set set_attack_seqs: Set of attack sequences used for duplicate detection.
    :param dict node_labels_dict: Mapping from node names to labels.
    :return set seqs_set: Set of sequences.
    :return dict nonattack_nodes_seqs_dict: Dictionary mapping combined nodes to sequences.
    """
    seqs_set = set()
    nonattack_nodes_seqs_dict = {}
    for comb_nodes in attack_nodes_list:
        # ls = [i for i in comb_nodes]
        set1 = set(comb_nodes)
        for node in nonattack_nodes:
            if node not in set1:
                # Extract and map sequences.
                edges = comb_nodes_edges_dict[comb_nodes]
                # Next, find edges to add: incoming and outgoing edges of node whose other endpoint is in comb_nodes.
                in_edges = graph.in_edges(node, keys=True, data=True)
                out_edges = graph.out_edges(node, keys=True, data=True)
                flag1 = False
                flag2 = False
                for edge in in_edges:
                    u, v, key, attr = edge
                    if u in comb_nodes:
                        edges.append((u, v, key, attr['type'], attr['start_time']))
                        flag1 = True
                for edge in out_edges:
                    u, v, key, attr = edge
                    if v in comb_nodes:
                        edges.append((u, v, key, attr['type'], attr['start_time']))
                        flag2 = True
                if flag1 or flag2:
                    edges = sorted(edges, key=lambda t: t[4])
                    s = get_sequence_nonattack_using_dict(edges, node_labels_dict)
                    if s not in set_attack_seqs:
                        seqs_set.add(s)
                        ls = [i for i in comb_nodes]
                        ls.append(node)
                        tuple1 = tuple(ls)
                        nonattack_nodes_seqs_dict[str(tuple1)] = s
    # ls = [i for i in seqs_set]
    return seqs_set, nonattack_nodes_seqs_dict

def sequence_construction(graph, attack_nodes):
    """Build sequences.

    :param _type_ graph: _description_
    :param _type_ attack_nodes: _description_
    :return _type_: _description_
    """
    
    attack_nodes_list = get_combinations(attack_nodes)
    print('len attack_nodes_list : ', len(attack_nodes_list))
    set_attack_seqs, comb_nodes_edges_dict = get_attack_sequence(graph, attack_nodes_list)
    print('len set_attack_seqs : ', len(set_attack_seqs))
    nonattack_nodes = set()
    for node in graph.nodes():
        if node not in attack_nodes:
            nonattack_nodes.add(node)
    print('len nonattack_nodes : ', len(nonattack_nodes))
    set_nonattack_seqs = get_nonattack_sequence_with_dict(graph, nonattack_nodes, comb_nodes_edges_dict, attack_nodes_list, set_attack_seqs)
    # set_nonattack_seqs = get_nonattack_sequence(graph, nonattack_nodes, attack_nodes_list, set_attack_seqs)
    return set_attack_seqs, set_nonattack_seqs, attack_nodes_list, nonattack_nodes
    # return set_attack_seqs


def sequence_construction_using_file(graph, attack_nodes, node_labels_dict, max_len=None):
    """Build sequences.

    :param _type_ graph: _description_
    :param _type_ attack_nodes: _description_
    :return _type_: _description_
    """
    
    attack_nodes_list = get_combinations(attack_nodes, max_len=max_len)
    print('len attack_nodes_list : ', len(attack_nodes_list))
    # set_attack_seqs, comb_nodes_edges_dict = get_attack_sequence(graph, attack_nodes_list)
    set_attack_seqs, comb_nodes_edges_dict, comb_nodes_seqs_dict = get_attack_sequence_using_dict(graph, attack_nodes_list, node_labels_dict)
    print('len set_attack_seqs : ', len(set_attack_seqs))
    nonattack_nodes = set()
    for node in graph.nodes():
        if node not in attack_nodes:
            nonattack_nodes.add(node)
    print('len nonattack_nodes : ', len(nonattack_nodes))
    # set_nonattack_seqs = get_nonattack_sequence_with_dict(graph, nonattack_nodes, comb_nodes_edges_dict, attack_nodes_list, set_attack_seqs)
    set_nonattack_seqs, nonattack_nodes_seqs_dict = get_nonattack_sequence_with_label_dict(graph, nonattack_nodes, comb_nodes_edges_dict, attack_nodes_list, set_attack_seqs, node_labels_dict)
    # set_nonattack_seqs = get_nonattack_sequence(graph, nonattack_nodes, attack_nodes_list, set_attack_seqs)
    return set_attack_seqs, set_nonattack_seqs, attack_nodes_list, nonattack_nodes, comb_nodes_seqs_dict, nonattack_nodes_seqs_dict
    # return set_attack_seqs

vocabs = {
        'system_file': 1,
        'lib_file'   : 2,
        'proc_file'  : 3,
        'temp_file'  : 4,
        'user_file'  : 5,
        'other_file' : 6,
        'system_process' : 7,
        'program_process' : 8,
        'user_process' : 9,
        'lib_process' : 10,
        'ip_address' : 11,
        'execve'    : 12,
        'clone' : 13,
        'write' : 14,
        'read'  : 15,
        'recvfrom' : 16,
        'write_vector' : 17,
        'sendto' : 18,
        'recvmsg' : 19,
    }
def atlas_embedding(seqs):
    # Build the vocabulary and convert sequences to the vocabulary's initial representation.
    # The maximum length is 400.
    # Vocabulary.
    embeddings_ls = []
    for seq in seqs:
        words = seq.split(' ')
        ls = []
        for word in words:
            if word in vocabs.keys():
                ls.append(vocabs[word])
            elif len(word) == 0:
                continue
            else:
                print(f"error : {word}, len = {len(word)}")
        embeddings_ls.append(ls)
    return embeddings_ls


def atlas_embedding_using_dict(comb_nodes_seqs_dict):
    # Build the vocabulary and convert sequences to the vocabulary's initial representation.
    # The maximum length is 400.
    # Vocabulary.
    embeddings_ls = []
    comb_nodes_embeddings_dict = {}
    for key, value in comb_nodes_seqs_dict.items():
        words = value.split(' ')
        ls = []
        for word in words:
            if word in vocabs.keys():
                ls.append(vocabs[word])
            elif len(word) == 0:
                continue
            else:
                print(f"error : {word}, len(word) = {len(word)}")
        embeddings_ls.append(ls)
        comb_nodes_embeddings_dict[key] = ls
    return embeddings_ls, comb_nodes_embeddings_dict


def get_test_seqs(graph, node_labels_dict, attack_nodes, nonattack_nodes):
    """Get test sequences.

    :param _type_ graph: _description_
    :param _type_ node_labels_dict: _description_
    :param _type_ attack_nodes: _description_
    :return _type_: _description_
    """
    # 1. Obtain subsets of non-attack entities. Because there can be many, use a threshold such as 20 to support at most 20 non-attack entities.
    # 2. Add attack entities to the non-attack entity subsets and obtain their sequences.
    
    # 1. The earlier interpretation was incorrect. First obtain the set of all unknown entities (non-attack entities here), i.e. the complete list of non-attack entities.
    #    Then obtain every single-element subset of this set, one for each list element.
    # 2. Obtain all non-empty subsets of attack entities, then add the subsets above to produce non-empty attack-entity subsets containing one unknown entity.
    # 3. Embed sequences.
    # 4. Test them with the model.

    max_len = 20    
    attack_nodes_list = get_combinations_max_len(attack_nodes, max_len)
    max_len_comb = len(attack_nodes)
    attack_nodes_list = []
    for i in range(1, max_len_comb + 1):
        ls1 = combinations(attack_nodes, i)
        for j in ls1:
            attack_nodes_list.append(j)
    print('len attack_nodes_list : ', len(attack_nodes_list))
    print(attack_nodes_list)
    print()
    print()
    ls1 = []
    for nonattack_node in nonattack_nodes:
        for attack_nodes in attack_nodes_list:
            ls = [i for i in attack_nodes]
            ls.append(nonattack_node)
            ls1.append(tuple(ls))
    # print(ls1)
    seqs_set, comb_nodes_edges_dict, comb_nodes_seqs_dict = get_attack_sequence_using_dict(graph, ls1, node_labels_dict)
    # set_attack_seqs, attack_nodes_seqs_dict = get_nonattack_sequence_with_label_dict(graph, attack_nodes, comb_nodes_edges_dict, attack_nodes_list, nonattack_seqs_set, node_labels_dict)
   
    return seqs_set #nonattack_nodes_list, comb_nodes_seqs_dict, attack_nodes_seqs_dict


def get_all_embeddings(attack_nodes_seqs_dict, nonattack_nodes_seqs_dict):
    attack_embeddings_ls, attack_comb_nodes_embeddings_dict = atlas_embedding_using_dict(attack_nodes_seqs_dict)
    nonattack_embeddings_ls, nonattack_comb_nodes_embeddings_dict = atlas_embedding_using_dict(nonattack_nodes_seqs_dict)
    return attack_embeddings_ls, nonattack_embeddings_ls, attack_comb_nodes_embeddings_dict, nonattack_comb_nodes_embeddings_dict



    
