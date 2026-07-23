#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
import argparse
import time

import numpy as np

if __package__:
    from .basic_funcs.graph_process import *
    from .basic_funcs.file_process import *
    from .basic_funcs.casuality import *
    from .basic_funcs.tools import *
    from .basic_funcs.get_config import *
    from .values import *
else:
    from basic_funcs.graph_process import *
    from basic_funcs.file_process import *
    from basic_funcs.casuality import *
    from basic_funcs.tools import *
    from basic_funcs.get_config import *
    from values import *


def back_analysis(poi_name, back_compressed_graph, gt_events, poi_event, need_print=False, need_save=False):
    save_path = fd_complement_path + poi_name + '/'
    # 3. Extract features.
    all_edges = sorted(back_compressed_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    windows_num = poi_names_windows_num_dict.get(poi_name, DEFAULT_WINDOWS_NUM)
    windows_graph_dict = get_time_windows(all_edges, windows_num)
    idf = get_idf(back_compressed_graph, windows_graph_dict)
    weights = feature_extraction(back_compressed_graph, poi_event, idf)
    weights = np.array(weights)
    set_idf = set()
    for weight in weights:
        set_idf.add(weight[3])
    # 4. Calculate edge weights.
    bcw_graph = weight_computation_without_lda(back_compressed_graph, weights)
    bcw_graph_name = 'bcw_graph'
    if need_save:
        save_graph(bcw_graph, save_path, bcw_graph_name)
        print(f'save bcw_graph {save_path + bcw_graph_name}.gz')
        weights_poi_name = 'weights.npy'
        save_2_npy(weights, save_path + weights_poi_name)
        print(f"save weights {save_path + weights_poi_name}")
    
    # 5. Backpropagate dependency impact.
    bcw_impact_graph = impact_propagation(bcw_graph, poi_event)
    if need_save:
        bcw_impact_graph_name = 'bcw_impact_graph'
        save_graph(bcw_impact_graph, save_path, bcw_impact_graph_name)
        print(f'save bcw_impact_graph {save_path + bcw_impact_graph_name}.gz')
    if need_print:
        print(f'weights : {weights.shape}; bcw_impact_graph: {bcw_impact_graph.number_of_nodes()}, {bcw_impact_graph.number_of_edges()};' +
          f'bcw_graph : {bcw_impact_graph.number_of_nodes()}, {bcw_impact_graph.number_of_edges()}'
          )
    # 6. Rank entry points.
    start_nodes_file, start_nodes_socket, start_nodes_process = get_sorted_three_entry_node(bcw_impact_graph)
    len_file = len(start_nodes_file)
    len_socket = len(start_nodes_socket)
    len_process = len(start_nodes_process)
    len_all_nodes = bcw_impact_graph.number_of_nodes()
    len_all_edges = bcw_impact_graph.number_of_edges()    
    if need_print:
        print('len_file, len_socket, len_process, len_gt-events,  use_len, len_all_nodes, len_all_edges')
        print(f'{len_file}, {len_socket}, {len_process}, {len(gt_events)}, {len_all_nodes}, {len_all_edges}')
        print('poi_name, number_i, num_of_nodes, len_fdgraph_nodes, len_fdgraph_edges, TP, FN, FP') 
    forward_graph = None
    number_i = 7
    start_nodes = get_start_nodes_with_score(start_nodes_file, start_nodes_socket, start_nodes_process, number_i)
    num_of_nodes = len(start_nodes)
    forward_graph = forward_analysis(bcw_impact_graph, start_nodes, num_of_nodes)
    if need_print:
        len_fdgraph_nodes = forward_graph.number_of_nodes()
        len_fdgraph_edges = forward_graph.number_of_edges()
        not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(forward_graph, gt_events)
        FP = len_fdgraph_edges - TP
        print(f'{poi_name}, {number_i}, {num_of_nodes}, {len_fdgraph_nodes}, {len_fdgraph_edges}, {TP}, {FN}, {FP}') 
    return forward_graph
    
times_dict = {}
def test_casuality_analysis_time(poi_name):
    print(f'\n\n-----{poi_name}------')
    path = None
    if poi_name in dot_file_names:
        path = graph_dot_path + 'back/' + poi_name + '.gz'
    else:
        path = graph_path_add_back + poi_name + '.gz'
    graph = read_graph(path)
    print(f'{graph.number_of_nodes()}, {graph.number_of_edges()}')
    gt_events = get_config_gt()[poi_name]
    poi_event = get_config_poiEs()[poi_name]
    start_time = time.time()
    back_compressed_graph = compress_graph(graph, max_time=10000)
    # if back_compressed_graph.number_of_edges() > 100000:
    #     back_compressed_graph = SementicCompress(back_compressed_graph)
    print(f'{back_compressed_graph.number_of_nodes()}, {back_compressed_graph.number_of_edges()}')
    
    print('compress ok')
    fd = back_analysis(poi_name, back_compressed_graph, gt_events, poi_event, need_print=True, need_save=False)
    end_time = time.time()
    print(f'{poi_name} cost time : {end_time - start_time} s')
    times_dict[poi_name] = end_time - start_time
    


def process_casuality_analysis(poi_name, back_compressed_graph, gt_events, poi_event, use_new=False, need_save=False):
    
    save_path = fd_complement_path + poi_name + '/'
    # 3. Extract features.
    all_edges = sorted(back_compressed_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    windows_num = poi_names_windows_num_dict.get(poi_name, DEFAULT_WINDOWS_NUM)
    windows_graph_dict = get_time_windows(all_edges, windows_num)
    idf = get_idf(back_compressed_graph, windows_graph_dict)
    weights = feature_extraction(back_compressed_graph, poi_event, idf)
    weights = np.array(weights)
    set_idf = set()
    for weight in weights:
        set_idf.add(weight[3])
    # 4. Calculate edge weights.
    bcw_graph = weight_computation(back_compressed_graph, weights, )
    bcw_graph_name = 'bcw_graph'
    if need_save:
        save_graph(bcw_graph, save_path, bcw_graph_name)
        print(f'save bcw_graph {save_path + bcw_graph_name}.gz')
        weights_poi_name = 'weights.npy'
        save_2_npy(weights, save_path + weights_poi_name)
        print(f"save weights {save_path + weights_poi_name}")
    
    # 5. Backpropagate dependency impact.
    bcw_impact_graph = impact_propagation(bcw_graph, poi_event)
    if need_save:
        bcw_impact_graph_name = 'bcw_impact_graph'
        save_graph(bcw_impact_graph, save_path, bcw_impact_graph_name)
        print(f'save bcw_impact_graph {save_path + bcw_impact_graph_name}.gz')
    
    print(f'weights : {weights.shape}; bcw_impact_graph: {bcw_impact_graph.number_of_nodes()}, {bcw_impact_graph.number_of_edges()};' +
          f'bcw_graph : {bcw_impact_graph.number_of_nodes()}, {bcw_impact_graph.number_of_edges()}'
          )
    
    
    # 6. Rank entry points.
    # start_nodes = entry_node_sort(bcw_impact_graph)
    start_nodes_file, start_nodes_socket, start_nodes_process = get_sorted_three_entry_node(bcw_impact_graph)
    # print(f'nodes = {bcw_impact_graph.number_of_nodes()}, edges = {bcw_impact_graph.number_of_edges()}')
    len_file = len(start_nodes_file)
    len_socket = len(start_nodes_socket)
    len_process = len(start_nodes_process)
    
    
    max_len = max(len_file, len_socket, len_process)
    # gt_events = gts_events[poi_name]
    # print('poi_name, number, len_graph_nodes, len_graph_edges, TP1, TP2, TP, FN, FP')
    
    
    len_all_nodes = bcw_impact_graph.number_of_nodes()
    len_all_edges = bcw_impact_graph.number_of_edges()
    # not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(bcw_impact_graph, gt_events)
    # print(f'bcw_impact_graph, {len_graph_nodes}, {len_graph_edges}, {TP1}, {TP2}, {TP}, {FN}, {len_graph_edges-TP}') 
    
    use_len = max_len + 1
    break_num = len_all_edges/2
    
    print('len_file, len_socket, len_process, len_gt-events, break_num, use_len, len_all_nodes, len_all_edges')
    print(f'{len_file}, {len_socket}, {len_process}, {len(gt_events)}, {break_num}, {use_len}, {len_all_nodes}, {len_all_edges}')
    print('poi_name, i, num_of_nodes, len_fdgraph_nodes, len_fdgraph_edges, TP, FN, FP') 
    forward_graph = None
    for i in range(1, use_len):
        start_nodes = get_start_nodes_with_score(start_nodes_file, start_nodes_socket, start_nodes_process, i)
        num_of_nodes = len(start_nodes)
        if use_new: 
            forward_graph = forward_analysis_new(bcw_impact_graph, start_nodes, num_of_nodes)
        else: 
            forward_graph = forward_analysis(bcw_impact_graph, start_nodes, num_of_nodes)
        len_fdgraph_nodes = forward_graph.number_of_nodes()
        len_fdgraph_edges = forward_graph.number_of_edges()
        not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(forward_graph, gt_events)
        FP = len_fdgraph_edges - TP
        # print(f'{poi_name}, ({len_all_nodes} {len_all_edges}), ({len_file} {len_socket} {len_process}), {i}, {num_of_nodes}, {len_fdgraph_nodes}, {len_fdgraph_edges}, {TP}, {FN}, {FP}') 
        print(f'{poi_name}, {i}, {num_of_nodes}, {len_fdgraph_nodes}, {len_fdgraph_edges}, {TP}, {FN}, {FP}') 
        # if FP > break_num or FP >= 500:
        #     break


def process_casuality_analysis_all12(poi_name, use_new=False):
    print(f'\n\n-----{poi_name}-----')
    back_compressed_graph_path = graph_path_complement + poi_name + '.gz'
    back_compressed_graph = read_graph(back_compressed_graph_path)
    print(f'back_compressed_graph node and edges: {poi_name}, {back_compressed_graph.number_of_nodes()}, {back_compressed_graph.number_of_edges()}')
    gt_events = get_config_gt()[poi_name]
    poi_event = get_config_poiEs()[poi_name]
    process_casuality_analysis(poi_name, back_compressed_graph, gt_events, poi_event, use_new=use_new)


def test_case7():
    path = graph_path_back_add_sem_compress + 'case7.gz'
    graph = read_graph(path)
    poi_name = 'case7'
    gt_events = get_config_gt()[poi_name]
    poi_event = get_config_poiEs()[poi_name]
    process_casuality_analysis(poi_name, graph, gt_events, poi_event)


def process_casuality_analysis_with_bcg_number(poi_name, back_compressed_graph, gt_events, poi_event, number, use_new=False, need_save=False):
    save_path = case_study_fd_path + poi_name + '/'
    # 3. Extract features.
    all_edges = sorted(back_compressed_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    windows_num = poi_names_windows_num_dict.get(poi_name, DEFAULT_WINDOWS_NUM)
    windows_graph_dict = get_time_windows(all_edges, windows_num)
    idf = get_idf(back_compressed_graph, windows_graph_dict)
    weights = feature_extraction(back_compressed_graph, poi_event, idf)
    weights = np.array(weights)
    set_idf = set()
    for weight in weights:
        set_idf.add(weight[3])
    # 4. Calculate edge weights.
    bcw_graph = weight_computation(back_compressed_graph, weights, )
    bcw_graph_name = 'bcw_graph'
    if need_save:
        save_graph(bcw_graph, save_path, bcw_graph_name)
        print(f'save bcw_graph {save_path + bcw_graph_name}.gz')
        weights_poi_name = 'weights.npy'
        save_2_npy(weights, save_path + weights_poi_name)
        print(f"save weights {save_path + weights_poi_name}")
    
    # 5. Backpropagate dependency impact.
    bcw_impact_graph = impact_propagation(bcw_graph, poi_event)
    if need_save:
        bcw_impact_graph_name = 'bcw_impact_graph'
        save_graph(bcw_impact_graph, save_path, bcw_impact_graph_name)
        print(f'save bcw_impact_graph {save_path + bcw_impact_graph_name}.gz')
    
    print(f'weights : {weights.shape}; bcw_impact_graph: {bcw_impact_graph.number_of_nodes()}, {bcw_impact_graph.number_of_edges()};' +
          f'bcw_graph : {bcw_impact_graph.number_of_nodes()}, {bcw_impact_graph.number_of_edges()}'
          )
    
    
    # 6. Rank entry points.
    # start_nodes = entry_node_sort(bcw_impact_graph)
    start_nodes_file, start_nodes_socket, start_nodes_process = get_sorted_three_entry_node(bcw_impact_graph)
    # print(f'nodes = {bcw_impact_graph.number_of_nodes()}, edges = {bcw_impact_graph.number_of_edges()}')
    len_file = len(start_nodes_file)
    len_socket = len(start_nodes_socket)
    len_process = len(start_nodes_process)
    
    
    max_len = max(len_file, len_socket, len_process)
    # gt_events = gts_events[poi_name]
    # print('poi_name, number, len_graph_nodes, len_graph_edges, TP1, TP2, TP, FN, FP')
    
    
    len_all_nodes = bcw_impact_graph.number_of_nodes()
    len_all_edges = bcw_impact_graph.number_of_edges()
    # not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(bcw_impact_graph, gt_events)
    # print(f'bcw_impact_graph, {len_graph_nodes}, {len_graph_edges}, {TP1}, {TP2}, {TP}, {FN}, {len_graph_edges-TP}') 
    
    use_len = max_len + 1
    break_num = len_all_edges/2
    
    print('len_file, len_socket, len_process, len_gt-events, break_num, use_len, len_all_nodes, len_all_edges')
    print(f'{len_file}, {len_socket}, {len_process}, {len(gt_events)}, {break_num}, {use_len}, {len_all_nodes}, {len_all_edges}')
    print('poi_name, i, num_of_nodes, len_fdgraph_nodes, len_fdgraph_edges, TP, FN, FP') 
    forward_graph = None
    forward_graph = None
    # for i in range(1, use_len):
    start_nodes = get_start_nodes_with_score(start_nodes_file, start_nodes_socket, start_nodes_process, number)
    num_of_nodes = len(start_nodes)
    if use_new: 
        forward_graph = forward_analysis_new(bcw_impact_graph, start_nodes, num_of_nodes)
    else: 
        forward_graph = forward_analysis(bcw_impact_graph, start_nodes, num_of_nodes)
    len_fdgraph_nodes = forward_graph.number_of_nodes()
    len_fdgraph_edges = forward_graph.number_of_edges()
    not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(forward_graph, gt_events)
    FP = len_fdgraph_edges - TP
    # print(f'{poi_name}, ({len_all_nodes} {len_all_edges}), ({len_file} {len_socket} {len_process}), {i}, {num_of_nodes}, {len_fdgraph_nodes}, {len_fdgraph_edges}, {TP}, {FN}, {FP}') 
    print(f'{poi_name}, {len_all_nodes}, {len_all_edges}, {number}, {num_of_nodes}, {len_fdgraph_nodes}, {len_fdgraph_edges}, {TP}, {FN}, {FP}')     
    save_graph(forward_graph, save_path, 'fd_graph')


def process_casuality_analysis_with_number(poi_name, bcw_impact_graph, gt_events, number, use_new=False):
    # 6. Rank entry points.
    # start_nodes = entry_node_sort(bcw_impact_graph)
    start_nodes_file, start_nodes_socket, start_nodes_process = get_sorted_three_entry_node(bcw_impact_graph)
    # print(f'nodes = {bcw_impact_graph.number_of_nodes()}, edges = {bcw_impact_graph.number_of_edges()}')
    # len_file = len(start_nodes_file)
    # len_socket = len(start_nodes_socket)
    # len_process = len(start_nodes_process)
    
    
    # max_len = max(len_file, len_socket, len_process)
    # gt_events = gts_events[poi_name]
    # print('poi_name, number, len_graph_nodes, len_graph_edges, TP1, TP2, TP, FN, FP')
    
    len_all_nodes = bcw_impact_graph.number_of_nodes()
    len_all_edges = bcw_impact_graph.number_of_edges()
    # not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(bcw_impact_graph, gt_events)
    # print(f'bcw_impact_graph, {len_graph_nodes}, {len_graph_edges}, {TP1}, {TP2}, {TP}, {FN}, {len_graph_edges-TP}') 
    
    # use_len = max_len + 1
    # break_num = len_all_edges/2
    
    # print('len_file, len_socket, len_process, len_gt-events, break_num, use_len, len_all_nodes, len_all_edges')
    # print(f'{len_file}, {len_socket}, {len_process}, {len(gt_events)}, {break_num}, {use_len}, {len_all_nodes}, {len_all_edges}')
    
    forward_graph = None
    # for i in range(1, use_len):
    start_nodes = get_start_nodes_with_score(start_nodes_file, start_nodes_socket, start_nodes_process, number)
    num_of_nodes = len(start_nodes)
    if use_new: 
        forward_graph = forward_analysis_new(bcw_impact_graph, start_nodes, num_of_nodes)
    else: 
        forward_graph = forward_analysis(bcw_impact_graph, start_nodes, num_of_nodes)
    len_fdgraph_nodes = forward_graph.number_of_nodes()
    len_fdgraph_edges = forward_graph.number_of_edges()
    not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(forward_graph, gt_events)
    FP = len_fdgraph_edges - TP
    # print(f'{poi_name}, ({len_all_nodes} {len_all_edges}), ({len_file} {len_socket} {len_process}), {i}, {num_of_nodes}, {len_fdgraph_nodes}, {len_fdgraph_edges}, {TP}, {FN}, {FP}') 
    print(f'{poi_name}, {len_all_nodes}, {len_all_edges}, {number}, {num_of_nodes}, {len_fdgraph_nodes}, {len_fdgraph_edges}, {TP}, {FN}, {FP}') 
    save_path = forward_graph_output_path
    
    save_graph(forward_graph, save_path, poi_name)

def func_for_case_study():
    all_poi_names1 = [  
    'fivedirections-case1', # Backward graph.
    'fivedirections-case3', # Backward graph edge 0.
    'case1', 
    'case7',
    ]
    num_dict = {
        'fivedirections-case1': 1,
        'fivedirections-case3': 7,
        'case1': 10, 
        'case7': 7,
    }
    for poi_name in all_poi_names1:
        print(f'-----{poi_name}-----')
        back_compressed_graph_path = case_study_back_compressed_path + poi_name + '.gz'
        
        back_compressed_graph = read_graph(back_compressed_graph_path)
        print(f'back_compressed_graph node and edges: {poi_name}, {back_compressed_graph.number_of_nodes()}, {back_compressed_graph.number_of_edges()}')
        gt_events = get_config_gt()[poi_name]
        poi_event = get_config_poiEs()[poi_name]
        number = num_dict[poi_name]
        # process_casuality_analysis_with_bcg_number(poi_name, back_compressed_graph, gt_events, poi_event, number, use_new=False, need_save=False)
        process_casuality_analysis(poi_name, back_compressed_graph, gt_events, poi_event, need_save=False)

def func_for_case_study1():
    all_poi_names1 = [  
    'fivedirections-case1', # Backward graph.
    'fivedirections-case3', # Backward graph edge 0.
    'case1', 
    'case7',
    ]
    num_dict = {
        'fivedirections-case1': 1,
        'fivedirections-case3': 7,
        'case1': 10, 
        'case7': 7,
    }
    poi_name = 'fivedirections-case3'
    print(f'-----{poi_name}-----')
    back_compressed_graph_path = case_study_back_compressed_path + poi_name + '.gz'
    
    back_compressed_graph = read_graph(back_compressed_graph_path)
    print(f'back_compressed_graph node and edges: {poi_name}, {back_compressed_graph.number_of_nodes()}, {back_compressed_graph.number_of_edges()}')
    gt_events = get_config_gt()[poi_name]
    poi_event = get_config_poiEs()[poi_name]
    number = num_dict[poi_name]
    process_casuality_analysis_with_bcg_number(poi_name, back_compressed_graph, gt_events, poi_event, number, use_new=False, need_save=True)
    # process_casuality_analysis(poi_name, back_compressed_graph, gt_events, poi_event, need_save=False)



def process_casuality_analysis_dot(poi_name, use_new_dict, number_dict):
    # print(f'\n\n-----{poi_name}-----')
    gt_events = get_config_gt()[poi_name]
    read_path = fd_complement_path + poi_name + '/'
    bcw_impact_graph = read_graph(read_path + 'bcw_impact_graph.gz')
    number = number_dict[poi_name]
    use_new = use_new_dict[poi_name]
    process_casuality_analysis_with_number(poi_name, bcw_impact_graph, gt_events, number, use_new=use_new)


# The following three test functions are somewhat disorganized.
def test_dot_graph(poi_name):
    # print(f'\n\n-----{poi_name}-----')
    graph_name = poi_name + '.gz'    
    need_add_graph_path = graph_dot_path_back_compressed + graph_name
    need_add_graph = read_graph(need_add_graph_path)
    len_nodes1 = need_add_graph.number_of_nodes()
    len_edges1 = need_add_graph.number_of_edges()
    
    origin_graph_path = graph_path_new_origin + graph_name
    origin_graph = read_graph(origin_graph_path)
    
    gt_events = get_config_gt()[poi_name]
    add_back_graph = add_edges(poi_name, need_add_graph, origin_graph, gt_events, need_compress=False)
    len_nodes2 = add_back_graph.number_of_nodes()
    len_edges2 = add_back_graph.number_of_edges()
    
    not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(add_back_graph, gt_events)
    
    FP = len_edges2 - TP
    print(f'{poi_name}, {len_nodes1}, {len_edges1}, {len_nodes2}, {len_edges2}, {TP}, {FN}, {FP}')
    save_graph(add_back_graph, graph_dot_path_back_add_compressed, poi_name)
def test_large_case_graph(poi_name):
    graph_name = poi_name + '.gz'
      
    graph_path = graph_path_back_add_sem_compress + graph_name
    graph_path = graph_path_complement + graph_name
    graph_path_complement
    # graph_path = graph_path_new_origin + graph_name
    
    back_compressed_graph = read_graph(graph_path)
    len_nodes1 = back_compressed_graph.number_of_nodes()
    len_edges1 = back_compressed_graph.number_of_edges()
    gt_events = get_config_gt()[poi_name]
    not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(back_compressed_graph, gt_events)
    print(f'{poi_name}, {len_nodes1}, {len_edges1}, {TP}, {FN}, {len_edges1-TP}')
def print_complement_graph(poi_name):
    graph_name = graph_path_complement + poi_name + '.gz'
    graph = read_graph(graph_name)
    gt_events = get_config_gt()[poi_name]
    print_graph_info(graph, poi_name, gt_events)


def main(argv=None):
    """Run the causality-analysis entry point."""
    parser = argparse.ArgumentParser(
        description="Run causality analysis for the cases defined in config.json."
    )
    parser.add_argument(
        "--config",
        help="Path to the experiment JSON file (defaults to project/config.json).",
    )
    parser.add_argument(
        "--poi",
        action="append",
        dest="poi_names",
        help="Run one POI/case name. Repeat this option to run multiple cases.",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Mirror console output to the configured output/logs directory.",
    )
    args = parser.parse_args(argv)

    if args.config:
        set_config_path(args.config)

    try:
        ground_truth = get_config_gt()
        poi_events = get_config_poiEs()
        poi_names_windows_num_dict.update(get_config_windows())
        metadata = get_config_metadata()
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    configured_names = sorted(set(ground_truth) | set(poi_events))
    incomplete_config = sorted(set(ground_truth) ^ set(poi_events))
    if incomplete_config:
        parser.error(
            "Cases missing ground_truth or poi_events configuration: "
            + ", ".join(incomplete_config)
        )

    configured_dot_names = metadata.get("dot_file_names", [])
    if not isinstance(configured_dot_names, list) or not all(
        isinstance(name, str) for name in configured_dot_names
    ):
        parser.error("metadata.dot_file_names must be a list of strings")
    for poi_name in configured_dot_names:
        if poi_name not in dot_file_names:
            dot_file_names.append(poi_name)

    selected_names = args.poi_names or all_poi_names or configured_names
    if not selected_names:
        parser.error("No cases are configured")

    unknown_names = [
        name
        for name in selected_names
        if name not in ground_truth or name not in poi_events
    ]
    if unknown_names:
        parser.error(
            "Unknown or incomplete cases: "
            + ", ".join(unknown_names)
        )

    if args.log:
        save_log(log_path_my, "causality-analysis")

    times_dict.clear()
    loop_func(test_casuality_analysis_time, selected_names)
    print("\nExecution times")
    for poi_name, elapsed_seconds in times_dict.items():
        print(f"{poi_name}, {elapsed_seconds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
