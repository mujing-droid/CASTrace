#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from basic_funcs.graph_process import *
from basic_funcs.file_process import *
from basic_funcs.casuality import *
from basic_funcs.tools import *
from basic_funcs.get_config import *
from values import *

# The feature_extraction function was modified here.
def depimpact(back_graph, poi_name, poi_event, min_start_nodes_num, need_save=False, print_start_nodes=False):
    save_path = depimpact_save_path + poi_name + '/'
    
    back_compressed_graph = remove_redundant_edges(back_graph, 10000)
    # 3. Extract features.
    all_edges = sorted(back_compressed_graph.edges(data=True, keys=True), key=lambda t: t[3].get('start_time', 1))
    weights = feature_extraction(back_compressed_graph, poi_event, idf=None, need_idf=False)
    weights = np.array(weights)
    print('weights ok')
    if need_save:
        save_2_npy(weights, save_path + 'weights.npy')
        print(f"save weights {save_path + 'weights.npy'}")
    # 4. Calculate edge weights.
    bcw_graph = weight_computation(back_compressed_graph, weights)
    print('bcw_graph ok')
    if need_save: 
        save_graph(bcw_graph, save_path, 'bcw_graph')
        print(f'save bcw_graph {poi_name}')
    
    # 5. Backpropagate dependency impact.
    bcw_impact_graph = impact_propagation(bcw_graph, poi_event)
    print('bcw_impact_graph ok')

    if need_save:
        save_graph(bcw_impact_graph, save_path, 'bcw_impact_graph')
        print(f'save bcw_impact_graph {poi_name}')

    
    # 6. Rank entry points.
    # start_nodes = entry_node_sort(bcw_impact_graph)
    start_nodes = get_sorted_entry_node(bcw_impact_graph)
    print(f'len(start_nodes) = {len(start_nodes)}')
    if print_start_nodes and len(start_nodes) <= 100:
        print(start_nodes)
    
    num_of_nodes1 = int(len(start_nodes) / 2)
    num_of_nodes2 = int(len(start_nodes) / 5)
    num_of_nodes3 = int(len(start_nodes) / 10)
    forward_graph = None
    # 7. Propagate forward to obtain the forward-analysis graph.
    print(f'num_of_nodes1 = {num_of_nodes1}, num_of_nodes2 = {num_of_nodes2}, num_of_nodes3 = {num_of_nodes3}')
    if len(start_nodes) <= min_start_nodes_num:
        num_of_nodes = len(start_nodes)
        forward_graph = forward_analysis(bcw_impact_graph, start_nodes, num_of_nodes)
        print('forward_graph.number_of_nodes() = ', forward_graph.number_of_nodes(), ', forward_graph.number_of_edges() = ', forward_graph.number_of_edges())
        if need_save:
            save_graph(forward_graph, save_path, 'forward_graph')
            print(f'save forward_graph {poi_name}')
    else :
        num_of_nodes = max(50, num_of_nodes1, num_of_nodes2, num_of_nodes3, 500)
        
        forward_graph = forward_analysis(bcw_impact_graph, start_nodes, num_of_nodes1)
        print('1 forward_graph.number_of_nodes() = ', forward_graph.number_of_nodes(), ', forward_graph.number_of_edges() = ', forward_graph.number_of_edges())
        # save_graph(forward_graph, forward_graph_path, poi_name + '-' + str(num_of_nodes1))
        if need_save:
            save_graph(forward_graph, save_path, 'forward_graph')
            print(f'save forward_graph {poi_name}')
        # forward_graph = forward_analysis(bcw_impact_graph, start_nodes, num_of_nodes2)
        # print('2 forward_graph.number_of_nodes() = ', forward_graph.number_of_nodes(), ', forward_graph.number_of_edges() = ', forward_graph.number_of_edges())
        # save_graph(forward_graph, forward_graph_path, poi_name + '-' + str(num_of_nodes2))
        
        # forward_graph = forward_analysis(bcw_impact_graph, start_nodes, num_of_nodes3)
        # print('3 forward_graph.number_of_nodes() = ', forward_graph.number_of_nodes(), ', forward_graph.number_of_edges() = ', forward_graph.number_of_edges())
        # save_graph(forward_graph, forward_graph_path, poi_name + '-' + str(num_of_nodes3))    
    return forward_graph


def depimpact1(bcw_impact_graph, poi_name, gt_events):
    save_path = depimpact_save_path + poi_name + '/'
    # 6. Rank entry points.
    # start_nodes = entry_node_sort(bcw_impact_graph)
    start_nodes_file, start_nodes_socket, start_nodes_process = get_sorted_three_entry_node(bcw_impact_graph)
    # print(f'len(start_nodes) = {len(start_nodes)}')
    # if print_start_nodes and len(start_nodes) <= 100:
    #     print(start_nodes)
    max_len = max(len(start_nodes_file), len(start_nodes_socket), len(start_nodes_process))
    number_nodes = bcw_impact_graph.number_of_nodes()
    number_edges = bcw_impact_graph.number_of_edges()
    break_num = number_edges / 2
    forward_graph = None
    fn, fp, tp = 0, 0, 0
    for number in range(1, max_len):
        start_nodes = get_start_nodes_with_score(start_nodes_file, start_nodes_socket, start_nodes_process, number)
        forward_graph = forward_analysis(bcw_impact_graph, start_nodes, len(start_nodes))
        fn, fp, tp = get_graph_fn_fp(forward_graph, gt_events_set=gt_events)
        print(f'{poi_name}, {number}, {number_nodes}, {number_edges}, {forward_graph.number_of_nodes()}, {forward_graph.number_of_edges()}, {fn}, {fp}, {tp}')
        if fp >= break_num or fp >= 10003: break
        # if fn == 0:
        #     break
    # save_graph(forward_graph, save_path, 'forward_graph')
    # print(f"{poi_name} : save forward_graph")
    return fn, fp, tp, number_edges


def test_func(poi_name):
    gt_events = get_config_gt()[poi_name]
    add_back_path = graph_path_add_back + poi_name + '.gz'
    add_back_graph = read_graph(add_back_path)
    not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(add_back_graph, gt_events)
    print(f'{poi_name}, {TP}, {TP1}, {TP2}, {FN}')
    
    new_back_path = graph_path_new_back + poi_name + '.gz'
    new_back_graph = read_graph(new_back_path)
    not_in_origin, TP, TP1, TP2, FN = is_gt_in_graph(new_back_graph, gt_events)
    print(f'{poi_name}, {TP}, {TP1}, {TP2}, {FN}')
    
times_dict = {}
def test_depimpact(poi_name):
    print(f'\n--------{poi_name}--------')
    
    if poi_name not in dot_file_names:
        return
    # add_back_path = graph_path_add_back + poi_name + '.gz'
    add_back_path = graph_dot_path_back + poi_name + '.gz'
    
    add_back_graph = read_graph(add_back_path)
    poi_event = get_config_poiEs()[poi_name]
    start_time = time.time()
    forward_graph = depimpact(add_back_graph, poi_name, poi_event, min_start_nodes_num=50, need_save=False, print_start_nodes=False)
    end_time = time.time()
    print(f'{poi_name}, number_of_nodes = {forward_graph.number_of_nodes()}, number_of_edges = {forward_graph.number_of_edges()}')
    print(f'cost time = {end_time - start_time:.4f}')
    times_dict[poi_name] = end_time - start_time
    gt_events = get_config_gt()[poi_name]
    fn, fp, tp = get_graph_fn_fp(forward_graph, gt_events_set=set(gt_events))
    print(f'{poi_name}, fn = {fn}, fp = {fp}, tp = {tp}')

ans_ls = []
def test_depimpact1(poi_name):
    bcw_impact_graph_path = depimpact_save_path + poi_name + '/' + graph_name_bcw_impact
    bcw_impact_graph = read_graph(bcw_impact_graph_path)
    gt_events = get_config_gt()[poi_name]
    fn, fp, tp, number_edges = depimpact1(bcw_impact_graph, poi_name, gt_events)
    ans_ls.append([poi_name, fp, fn, number_edges])

def test_forward_fn_fp(poi_name):
    forward_graph = read_graph(depimpact_save_path + poi_name + '/' + graph_name_forward)
    # print(f'{poi_name}, number_of_nodes = {forward_graph.number_of_nodes()}, number_of_edges = {forward_graph.number_of_edges()}')
    gt_events = get_config_gt()[poi_name]
    fn, fp, tp = get_graph_fn_fp(forward_graph, gt_events_set=set(gt_events))
    print(f'{poi_name}, {fp}, {fn}, {forward_graph.number_of_edges()}')


if __name__ == '__main__':
    # print('main')
    # log_file_name = 'Results for the counts of three entry-point categories'
    # save_log(log_path_depimpact, log_file_name)
    # loop_func(test_func, all_poi_names=all_poi_names)
    # loop_func(test_depimpact, all_poi_names)
    # print('poi_name, number, number_nodes, number_edges, fn, fp, tp')
    # loop_func(test_depimpact1, all_poi_names)
    
    # log_file_name = 'forward_edges_fn_fp'
    # save_log(log_path_depimpact, log_file_name)
    # loop_func(test_forward_fn_fp, all_poi_names)
    
    # log_file_name = 'forward_edges_fn_fp'
    # save_log(log_path_depimpact, log_file_name)
    # loop_func(test_depimpact1, all_poi_names)
    # print(f'poi_name, fp, fn, number_edges')
    # for i in ans_ls:
    #     print(f'{i[0]}, {i[1]}, {i[2]}, {i[3]}')
    
    # log_file_name = 'forward_edges_fn_fp'
    # save_log(log_path_depimpact, log_file_name)
    # loop_func(test_forward_fn_fp, all_poi_names)
    
    # log_file_name = 'entry_point_ans'
    # save_log(log_path_depimpact, log_file_name)
    # loop_func(test_depimpact1, all_poi_names)
    
    # log_file_name = 'forward_edges_fn_fp'
    # save_log(log_path_depimpact, log_file_name)
    # loop_func(test_forward_fn_fp, all_poi_names)
    
    # log_file_name = 'eight_forward_edges_fn_fp'
    # save_log(log_path_depimpact, log_file_name)
    # all_poi_names1 = [
    # 'fivedirections-case1', # Backward graph.
    # 'fivedirections-case3', # Backward graph edge 0.
    # 'theia-case1', # Backward graph edge 0.
    # 'theia-case3', # Backward graph edge 0.
    # 'case2',
    # 'case3',
    # 'case4',
    # 'case5',
    # ]
    # loop_func(test_depimpact1, all_poi_names1)
    
    log_file_name = '测时间'
    save_log(log_path_depimpact, log_file_name)
    loop_func(test_depimpact, all_poi_names)
    print('\n\ntimes_dict')
    for k, v in times_dict.items():
        print(f'{k}, {v}')
