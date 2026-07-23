#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import networkx as nx
import math
import warnings


def find_sequences_all(G):
    """
    Find all sequences in the graph and sort them by time.
    :param G:
    :return: Dictionary mapping each process to an event list: {process1: [e1, e2, ...]}.
    """
    sequences = {}
    for node in G.nodes():
        # print(node)
        if G.nodes[node]['type'] == 'process':
            sequences[node] = []
            set_events_node = set()
            in_events = G.in_edges(node, data=True, keys=True)
            out_events = G.out_edges(node, data=True, keys=True)
            for e in in_events:
                u, v, key = e[0], e[1], e[2]
                set_events_node.add((u, v, key))
            # sequences[node].append(e)
            for e in out_events:
                u, v, key = e[0], e[1], e[2]
                set_events_node.add((u, v, key))
            # sequences[node].append(e)
            for e in set_events_node:
                u, v, key = e[0], e[1], e[2]
                attr = G.adj[u][v][key]
                sequences[node].append((u, v, key, attr))

    # len_events = 0
    # event_set = set()
    # print('len(sequences) = ', len(sequences))
    # for key, value in sequences.items():
    #     len_events += len(value)
    #     # print(f'{key}, {len(value)}')
    #     # print('key = ', key, ', len(value) = ', len(value))
    #     for event in sequences[key]:
    #         u, v, key = event[0], event[1], event[2]
    #         event_set.add((u, v, key))
    #
    # print('len_events = ', len_events)
    # print('len(sequences) = ', len(sequences), 'len_events = ', len_events, 'len(event_set) = ', len(event_set))
    return sequences


def have_blankspace(s):
    """
        Check whether a string contains spaces, remove them if present, and return the resulting string.
    """
    if ' ' in s:
        s1 = ''
        ls = s.strip().split(' ')
        for i in ls:
            s1 += i
    return s


def vocab_process(node_name, process_set, ls_node):
    """
        Process a node name by removing spaces and splitting it on underscores and slashes.
        e.g. 
        bash_8292 -> bash 8292
        Program_9012 -> Program 9012
        
    Args:
        node_name (_type_): _description_
        process_set (_type_): _description_
        ls_node (_type_): _description_
    """
    flag = 0
    if '_' in node_name:
        if '\\' in node_name:
            x = node_name.split('\\')
            index1 = 1
            x[0] = have_blankspace(x[0])
            process_set.add(x[0])
            ls_node.append(x[0])
            while index1 < len(x) - 1:
                x[index1] = have_blankspace(x[index1])
                process_set.add(x[index1])
                ls_node.append(x[index1])
                index1 += 1
            if '_' in x[index1]:
                x[index1] = have_blankspace(x[index1])
                process_set.add(x[index1].split('_')[0])
                process_set.add(x[index1].split('_')[1])
                ls_node.append(x[index1].split('_')[0])
                ls_node.append(x[index1].split('_')[1])
            else:
                print('*******process有_ and \\，但最后一个没_ *******')
                flag = 1
                # other_ls.append(node)
        elif '/' in node_name:
            x = node_name.split('/')
            index1 = 1
            if len(x[0]) > 0:
                x[0] = have_blankspace(x[0])
                process_set.add(x[0])
                ls_node.append(x[0])
            while index1 < len(x) - 1:
                x[index1] = have_blankspace(x[index1])
                process_set.add(x[index1])
                ls_node.append(x[index1])
                index1 += 1
            if '_' in x[index1]:
                x[index1] = have_blankspace(x[index1])
                process_set.add(x[index1].split('_')[0])
                process_set.add(x[index1].split('_')[1])
                ls_node.append(x[index1].split('_')[0])
                ls_node.append(x[index1].split('_')[1])
            else:
                print('*******process有_ and /，但最后一个没_ *******')
                flag = 2
                # other_ls.append(node)
        else:
            x = node_name.split('_')
            
            index1 = 1
            process_set.add(x[0])
            ls_node.append(x[0])
            x[0] = have_blankspace(x[0])
            while index1 < len(x):
                x[index1] = have_blankspace(x[index1])
                process_set.add(x[index1])
                ls_node.append(x[index1])
                index1 += 1
            # if len(x) > 2:
            #     print('*******process contains _ but no \\ or /, and len(x) > 2*******: ', node)
            # other_ls.append(node)
    else:
        print('*******process 没有_ *******')
        flag = 3
        # other_ls.append(node)
    return flag


def vocab_network(node_name, ip_set, ls_node):
    """
        Process a network node by removing spaces from its name and splitting it on underscores and slashes.
        e.g. 
        10.12.13.128:8091->11.14.12.38:1234  => 10 12 13 128 8091 11 14 12 38 1234
        10.12.13.128->11.14.12.38  => 10 12 13 128 11 14 12 38
        null:5965->null: 0  => null 5965 null 0
        10.12.13.128:5965->null: 0  => 10 12 13 128 5965 null 0
    Args:
        node_name (_type_): _description_
        ip_set (_type_): _description_
        ls_node (_type_): _description_
    """
    flag = 0
    if '->' in node_name:
        x2 = node_name.split('->')
        if len(x2) != 2:
            print('******* socket 分割长度不为2 *******')
            flag = 1
            # other_ls.append(node)
        else:
            src, des = x2[0], x2[1]
            # try:
            if 'null' not in src:
                if ':' in src:
                    src_ip, src_port = src.split(':')[0], src.split(':')[1]
                    src_ip_nums = src_ip.split('.')
                    ip_set.add(src_port)
                    ip_set.add(src_ip_nums[0])
                    ls_node.append(src_ip_nums[0])
                    index1 = 1
                    while index1 < 4:
                        ip_set.add(src_ip_nums[index1])
                        ls_node.append(src_ip_nums[index1])
                        index1 += 1
                    ls_node.append(src_port)
                else :
                    src_ip_nums = src.split('.')
                    ip_set.add(src_ip_nums[0])
                    ls_node.append(src_ip_nums[0])
                    index1 = 1
                    while index1 < len(src_ip_nums):
                        ip_set.add(src_ip_nums[index1])
                        ls_node.append(src_ip_nums[index1])
                        index1 += 1
            else:
                # null:5965->null: 0
                src_ip, src_port = src.split(':')[0], src.split(':')[1]
                ip_set.add(src_ip)
                ip_set.add(src_port)
                ls_node.append(src_ip)
                ls_node.append(src_port)
            if 'null' not in des:
                if ':' in des:
                    des_ip, des_port = des.split(':')[0], des.split(':')[1]
                    des_ip_nums = des_ip.split('.')
                    ip_set.add(des_port)
                    index1 = 1
                    ip_set.add(des_ip_nums[0])
                    ls_node.append(des_ip_nums[0])
                    while index1 < 4:
                        ip_set.add(des_ip_nums[index1])
                        ls_node.append(des_ip_nums[index1])
                        index1 += 1
                    ls_node.append(des_port)
                else:
                    des_ip_nums = des.split('.')
                    index1 = 1
                    ip_set.add(des_ip_nums[0])
                    ls_node.append(des_ip_nums[0])
                    while index1 < len(src_ip_nums):
                        ip_set.add(des_ip_nums[index1])
                        ls_node.append(des_ip_nums[index1])
                        index1 += 1
            else:  # null:5965->null: 0
                des_ip, des_port = des.split(':')[0], des.split(':')[1]
                ip_set.add(des_port)
                ip_set.add( des_ip)
                ls_node.append(des_ip)
                ls_node.append(des_port)
            # except Exception as e:
            #     print('ERROR *** ', e, ' *******')
            #     print(node)
    else:
        print('******* socket 不包含 -> *******')
        flag = 2
        # other_ls.append(node)
    return flag


def vocab_file(node_name, file_set, ls_node):
    """
        Process a file node by removing spaces from its name and splitting it on backslashes and double slashes.
        (The slash must be doubled here to avoid an error.)
            SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes in position 348-349: truncated \\UXXXXXXXX escape
        )
        e.g. 
        Users/Administrator/Desktop/test.txt => Users Administrator Desktop test txt
        usr/pwd/pwd1.pw => usr pwd pwd1.pw
    Args:
        node_name (_type_): _description_
        file_set (_type_): _description_
        ls_node (_type_): _description_
    """
    flag = 0
    if '\\' in node_name:
        x = node_name.split('\\')
        index1 = 1
        x[0] = have_blankspace(x[0])
        file_set.add(x[0])
        ls_node.append(x[0])
        while index1 < len(x):
            x[index1] = have_blankspace(x[index1])
            file_set.add(x[index1])
            ls_node.append(x[index1])
            index1 += 1
    elif '/' in node_name:
        x = node_name.split('/')
        index1 = 1
        if len(x[0]) > 0:
            x[0] = have_blankspace(x[0])
            file_set.add(x[0])
            ls_node.append(x[0])
        while index1 < len(x):
            x[index1] = have_blankspace(x[index1])
            file_set.add(x[index1])
            ls_node.append(x[index1])
            index1 += 1
    elif ':' in node_name:
        x = node_name.split(':')
        index1 = 1
        x[0] = have_blankspace(x[0])
        file_set.add(x[0])
        ls_node.append(x[0])
        while index1 < len(x):
            x[index1] = have_blankspace(x[index1])
            file_set.add(x[index1])
            ls_node.append(x[index1])
            index1 += 1
    else:
        print('*******file 没有\\ or / or : *******')
        # other_ls.append(node)
        flage = 1
    return flag


def create_vocab_from_graph(G):
    """
        Create a token vocabulary directly from the graph.
        :param G: Graph.
        :return:
                ls_all: Token list [s1, s2, ...], where s may be '.12', etc.
                dict_vocabs: Dictionary mapping processes to tokens.

        To simplify tokenization, use have_blankspace to detect and remove spaces.
    """
    process_set = set()
    type_set = set()
    file_set = set()
    ip_set = set()
    other_ls = []
    dict_vocabs = {}
    for node in G.nodes(data=True):
        node_name = node[0]
        dict_vocabs[node_name] = []
        ls_node = []
        if len(node_name) == 0:
            continue
        if node[1]['type'] == 'process': # Process nodes.
            flag = vocab_process(node_name, process_set, ls_node)
            if flag != 0:
                other_ls.append(node)
        elif node[1]['type'] == 'socket':
            flag = vocab_network(node_name, ip_set, ls_node)
            if flag != 0:
                other_ls.append(node)
        elif node[1]['type'] == 'file':
            flag = vocab_file(node_name, file_set, ls_node)
            if flag != 0:
                other_ls.append(node)
        else:
            print('******* 类型不是上面的三种 *******')
            other_ls.append(node)
        dict_vocabs[node_name] = ls_node
    for e in G.edges(data=True):
        type_set.add(e[2]['type'])
    ls_all = []
    # ! all_set appears to be redundant here.
    all_set = set()
    for i in process_set:
        all_set.add(i)
    del process_set
    for i in type_set:
        all_set.add(i)
    del type_set
    for i in file_set:
        all_set.add(i)
    del file_set
    for i in ip_set:
        all_set.add(i)
    del ip_set
    for i in all_set:
        if i is not None and len(i) > 0:
            ls_all.append(i)
    if len(other_ls) > 0:
        print('============== create-vocabs ================')
        print('len(other_ls) = ', len(other_ls))
        for i in other_ls:
            print(i)
        print('============== create-vocabs ================')
    return ls_all, dict_vocabs


def add_sequences(s, ls, u, v, type, node_vocabs, max_length=510):
    """
        Obtain tokenized results directly from process-centered sequences because using the tokenizer is very time-consuming.
    :param s: Previous sequence.
    :param ls: Previous token sequence; it is modified directly because it is passed by reference.
    :param u: Source node.
    :param v: Destination node.
    :param type: Event type.
    :param node_vocabs: Mapping between node names and tokens.
    :param max_length: Maximum token length; 510 leaves room for CLS and SEP.
    :return: s : '10 .12 .135 .123 :80 ->12 .34 .53 .125 :100 type1 C: //program _8093 ......'
        s1: New word produced after the token count exceeds max_length.
        ls1: New token sequence produced after the length exceeds max_length.
        
    """
    if u not in node_vocabs.keys():
        print(u, ' not in node_vocabs.keys()')
        return None
    if v not in node_vocabs.keys():
        print(v, ' not in node_vocabs.keys()')
        return None
    u_vocabs = node_vocabs[u]
    v_vocabs = node_vocabs[v]
    len_ls = len(ls)
    i, len_u, len_v = 0, len(u_vocabs), len(v_vocabs)
    ls_1 = []
    len_ls1 = 0
    s1 = ''
    # if len_ls >= max_length or len_ls + len_u + len_v + 1 > max_length:  
    if len_ls >= max_length or len_ls + len_u + len_v + 1 > max_length:
        # The length exceeds max_length; create a new sequence directly.
        for j in u_vocabs:
            ls_1.append(j)
            s1 += (' ' + j)
        ls_1.append(type)
        s1 += (' ' + type)
        for j in v_vocabs:
            ls_1.append(j)
            s1 += (' ' + j)
        return {'s': s, 's1': s1, 'ls_1': ls_1}
    # The length does not exceed max_length, so append it directly.
    for j in u_vocabs:
        ls.append(j)
        s += (' ' + j)
    ls.append(type)
    s += (' ' + type)
    for j in v_vocabs:
        ls.append(j)
        s += (' ' + j)
    return {'s': s.strip(), 's1': s1.strip(), 'ls_1': ls_1}


def find_process_sequences(all_sequences, node_vocabs, max_time_sequence=10000):
    """
        Tokenize sequences and remove duplicates.
        :param all_sequences:
        :param max_time_sequence:
        :return: 
            all_seq_dict: List of tokenized sequence strings [s1, s2, ...], where s may be "A type1 B B type2 C ...".
            len(set_word_seqs) 
            e.g.
            'Program_7620' : [
                ['C: Program 7620 clone C: Program 7620'], 
                ['C: Program 7620 clone C: Program 7620 C: Program 2836 clone C: Program 7620']
            ]
    """
    # Tokenize sequences: (u, v, start_time, type, end_time, data_amount).
    # There are two methods; method 1 is currently preferred.
    # 1. u type v; v type v1 ... Use file paths, IP addresses, and process names directly.
    # 2. u_type type v_type; v_type type v1_type ... Classify entities as ATLAS does.
    
    pro_seq_dict = {}
    # word_seq_e = []
    # Split all sequences by time.
    for key, value in all_sequences.items():
        pro_seq_dict[key] = []
        events = sorted(value, key=lambda x: x[3]['start_time'])
        i, len_events, word_sequence_key, ls1 = 0, len(events), [], []
        # ls1 previously used OrderedSet for deduplication, but this could remove entries from (a,b,type1), (a,c,type1), (a,b,type1), ...
        # It removes the later (a,b,type1), so use ls instead.
        # ls1 = OrderedSet()
        if len_events <= 0:
            # print('key = ', key, 'len_events <= 0')
            continue
        u1, v1, type1, time = events[i][0], events[i][1], events[i][3]['type'], events[i][3]['start_time']
        if len_events == 1:
            # If len(value) is 0, append directly.
            ls1 = [[(u1, v1, type1)]]
            # ls1 = [[(u1, v1, type1)]] means the current process has only one sequence, [(u1, v1, type1)], containing a single event.
            pro_seq_dict[key] = ls1
            # word_seq_e.append(ls1)
            continue
        ls1.append((u1, v1, type1))
        i += 1
        while i < len_events:
            time1 = events[i - 1][3]['start_time']
            u2, v2, type2, time2 = events[i][0], events[i][1], events[i][3]['type'], events[i][3]['start_time']
            time1 = float(time1)
            time2 = float(time2)
            if time1 > time2:
                print('ERROR : *********key = ', key, ', 不是升序的*********')
                break
            if time2 - time1 < max_time_sequence:
                ls1.append((u2, v2, type2))
            else:
                word_sequence_key.append(ls1)
                ls1 = [(u2, v2, type2)]
            i += 1
        word_sequence_key.append(ls1)
        pro_seq_dict[key] = word_sequence_key
        # word_seq_e.append(word_sequence_key)
    # Obtain the split sequences and then tokenize them.
    # all_seq_ls = []
    all_seq_dict = {}
    process_num = 0
    set_word_seqs = set()
    len_all_seq_dict = 0
    # Record sequences in the word_sequences set to prevent duplicates.
    for key, seqs in pro_seq_dict.items():
        # key is the process name, and value contains all sequences for that process.
        # ! A rewrite bug on 2024-07-04 at 13:56:49 took over two hours to trace to this line; use seqs directly.
        # seqs = value
        # seqs contains all sequences for one process: [[sequence 1], [sequence 2], ...].
        process_seq = []
        process_num += 1
        for seq in seqs:
            # seq is one sequence's events in chronological order: [sequence 1], [sequence 2], ...
            s, s1, ls, ls_1 = '', '', [], []
            for event in seq:
                # event is an individual event in the sequence: (u, v, type).
                ls_all_breaks = []
                u, v, type1 = event[0], event[1], event[2]
                dict_s = add_sequences(s, ls, u, v, type1, node_vocabs)
                if dict_s is not None:
                    s, s1, ls_1 = dict_s['s'], dict_s['s1'], dict_s['ls_1']
                    if s not in set_word_seqs:
                        set_word_seqs.add(s)
                        ls_all_breaks.append(s)
                    if len(s1) > 0:
                        if s1 not in set_word_seqs:
                            set_word_seqs.add(s1)
                            ls_all_breaks.append(s1)
                        s = s1
                        ls = ls_1
                if len(ls_all_breaks) > 0:
                    process_seq.append(ls_all_breaks)
                    len_all_seq_dict += len(ls_all_breaks)
        # all_seq_ls.append(process_seq)
        all_seq_dict[key] = process_seq
    # print(len(set_word_seqs))
    # print(len(all_seq_ls))
    # print(process_num)
    # len(set_word_seqs)
    return all_seq_dict, len_all_seq_dict


def find_process_sequences1(all_sequences, node_vocabs, max_time_sequence=10000, flag=True):
    """
    New version that builds on the previous implementation to obtain sequences corresponding to events.
        Tokenize sequences and remove duplicates.
        :param all_sequences:
        :param max_time_sequence:
        :return: 
            all_seq_dict: List of tokenized sequence strings [s1, s2, ...], where s may be "A type1 B B type2 C ...".
            len(set_word_seqs) 
            e.g.
            'Program_7620' : [
                ['C: Program 7620 clone C: Program 7620'], 
                ['C: Program 7620 clone C: Program 7620 C: Program 2836 clone C: Program 7620']
            ]
    """
    # Tokenize sequences: (u, v, start_time, type, end_time, data_amount).
    # There are two methods; method 1 is currently preferred.
    # 1. u type v; v type v1 ... Use file paths, IP addresses, and process names directly.
    # 2. u_type type v_type; v_type type v1_type ... Classify entities as ATLAS does.
    
    pro_seq_dict = {}
    # word_seq_e = []
    event_seqs = {} # key: (u,v,key); value: [sequence 1, sequence 2, ...].
    # Split all sequences by time.
    for key, value in all_sequences.items():
        pro_seq_dict[key] = []
        events = sorted(value, key=lambda x: x[3]['start_time'])
        i, len_events, word_sequence_key, ls1 = 0, len(events), [], []
        # ls1 previously used OrderedSet for deduplication, but this could remove entries from (a,b,type1), (a,c,type1), (a,b,type1), ...
        # It removes the later (a,b,type1), so use ls instead.
        # ls1 = OrderedSet()
        if len_events <= 0:
            # print('key = ', key, 'len_events <= 0')
            continue
        u1, v1, type1, time, event_key = events[i][0], events[i][1], events[i][3]['type'], events[i][3]['start_time'], events[i][2]
        if len_events == 1:
            # If len(value) is 0, append directly.
            ls1 = [[(u1, v1, type1, event_key)]]
            # ls1 = [[(u1, v1, type1)]] means the current process has only one sequence, [(u1, v1, type1)], containing a single event.
            pro_seq_dict[key] = ls1
            # word_seq_e.append(ls1)
            if (u1, v1, event_key) not in event_seqs.keys():
                event_seqs[str((u1, v1, event_key))] = []
            continue
        ls1.append((u1, v1, type1, event_key))
        i += 1
        while i < len_events:
            time1 = events[i - 1][3]['start_time']
            u2, v2, type2, time2, event_key = events[i][0], events[i][1], events[i][3]['type'], events[i][3]['start_time'], events[i][2]
            if (u2, v2, event_key) not in event_seqs.keys():
                event_seqs[str((u2, v2, event_key))] = []
            time1 = float(time1)
            time2 = float(time2)
            if time1 > time2:
                print('ERROR : *********key = ', key, ', 不是升序的*********')
                break
            if time2 - time1 < max_time_sequence:
                ls1.append((u2, v2, type2, event_key))
            else:
                word_sequence_key.append(ls1)
                ls1 = [(u2, v2, type2, event_key)]
            i += 1
        word_sequence_key.append(ls1)
        pro_seq_dict[key] = word_sequence_key
        # word_seq_e.append(word_sequence_key)
    # Obtain the split sequences and then tokenize them.
    # all_seq_ls = []
    all_seq_dict = {}
    process_num = 0
    set_word_seqs = set()
    len_all_seq_dict = 0
    # Record sequences in the word_sequences set to prevent duplicates.
    for key, seqs in pro_seq_dict.items():
        # key is the process name, and value contains all sequences for that process.
        # ! A rewrite bug on 2024-07-04 at 13:56:49 took over two hours to trace to this line; use seqs directly.
        # seqs = value
        # seqs contains all sequences for one process: [[sequence 1], [sequence 2], ...].
        process_seq = []
        process_num += 1
        for seq in seqs:
            # seq is one sequence's events in chronological order: [sequence 1], [sequence 2], ...
            s, s1, ls, ls_1 = '', '', [], []
            for event in seq:
                # event is an individual event in the sequence: (u, v, type).
                ls_all_breaks = []
                u, v, type1, event_key = event[0], event[1], event[2], event[3]
                if (u, v, event_key) not in event_seqs.keys():
                    event_seqs[str((u, v, event_key))] = []
                    
                dict_s = add_sequences(s, ls, u, v, type1, node_vocabs)
                if dict_s is not None:
                    s, s1, ls_1 = dict_s['s'], dict_s['s1'], dict_s['ls_1']
                    if flag or s not in set_word_seqs:
                        set_word_seqs.add(s)
                        ls_all_breaks.append(s)
                        event_seqs[str((u,v,event_key))].append(s)
                    if len(s1) > 0:
                        if flag or s1 not in set_word_seqs:
                            set_word_seqs.add(s1)
                            ls_all_breaks.append(s1)
                            event_seqs[str((u,v,event_key))].append(s1)
                        s = s1
                        ls = ls_1
                if len(ls_all_breaks) > 0:
                    process_seq.append(ls_all_breaks)
                    len_all_seq_dict += len(ls_all_breaks)
        # all_seq_ls.append(process_seq)
        all_seq_dict[key] = process_seq
    # print(len(set_word_seqs))
    # print(len(all_seq_ls))
    # print(process_num)
    # len(set_word_seqs)
    return all_seq_dict, len_all_seq_dict, event_seqs



def find_process_sequences_all(all_sequences, max_time_sequence=10000):
    """
        Tokenize sequences and remove duplicates.
        :param all_sequences:
        :param max_time_sequence:
        :return: 
            all_seq_dict: List of tokenized sequence strings [s1, s2, ...], where s may be "A type1 B B type2 C ...".
            len(set_word_seqs) 
            e.g.
            'Program_7620' : [
                ['C: Program 7620 clone C: Program 7620'], 
                ['C: Program 7620 clone C: Program 7620 C: Program 2836 clone C: Program 7620']
            ]
    """
    # Tokenize sequences: (u, v, start_time, type, end_time, data_amount).
    # There are two methods; method 1 is currently preferred.
    # 1. u type v; v type v1 ... Use file paths, IP addresses, and process names directly.
    # 2. u_type type v_type; v_type type v1_type ... Classify entities as ATLAS does.
    
    pro_seq_dict = {}
    # word_seq_e = []
    # Split all sequences by time.
    for key, value in all_sequences.items():
        pro_seq_dict[key] = []
        events = sorted(value, key=lambda x: x[3]['start_time'])
        i, len_events, word_sequence_key, ls1 = 0, len(events), [], []
        # ls1 previously used OrderedSet for deduplication, but this could remove entries from (a,b,type1), (a,c,type1), (a,b,type1), ...
        # It removes the later (a,b,type1), so use ls instead.
        # ls1 = OrderedSet()
        if len_events <= 0:
            print('key = ', key, 'len_events <= 0')
            continue
        u1, v1, type1, time = events[i][0], events[i][1], events[i][3]['type'], events[i][3]['start_time']
        if len_events == 1:
            # If len(value) is 0, append directly.
            ls1 = [[(u1, v1, type1)]]
            # ls1 = [[(u1, v1, type1)]] means the current process has only one sequence, [(u1, v1, type1)], containing a single event.
            pro_seq_dict[key] = ls1
            # word_seq_e.append(ls1)
            continue
        ls1.append((u1, v1, type1))
        i += 1
        while i < len_events:
            time1 = events[i - 1][3]['start_time']
            u2, v2, type2, time2 = events[i][0], events[i][1], events[i][3]['type'], events[i][3]['start_time']
            time1 = float(time1)
            time2 = float(time2)
            if time1 > time2:
                print('ERROR : *********key = ', key, ', 不是升序的*********')
                break
            if time2 - time1 < max_time_sequence:
                ls1.append((u2, v2, type2))
            else:
                word_sequence_key.append(ls1)
                ls1 = [(u2, v2, type2)]
            i += 1
        word_sequence_key.append(ls1)
        pro_seq_dict[key] = word_sequence_key
        # word_seq_e.append(word_sequence_key)
    return pro_seq_dict


def find_break_sequences_from_sequences(all_sequences, node_vocabs, max_time_sequence=10000):
    warnings.warn("忘了是干嘛的，用find_word_sequences_break",
                  DeprecationWarning
                 )
    """
    This appears to obtain text sequences directly.
    :param _type_ all_sequences: _description_
    :param _type_ node_vocabs: _description_
    :param int max_time_sequence: _description_, defaults to 10000
    :return _type_: _description_
    """
    word_sequences = []
    all_word_sequences = []
    string_set = set()
    for key, value in all_sequences.items():
        all_s = ''
        events = sorted(value, key=lambda x: x[3]['start_time'])
        len_events = len(events)
        word_sequence_key = []
        sequences_now = []
        # ls = []
        if len_events <= 0:
            print('key = ', key, 'len_events <= 0')
            continue
        i = 0
        u, v, type, time = events[i][0], events[i][1], events[i][3]['type'], events[i][3]['start_time']
        s, ls, s1, ls_1 = '', [], '', []
        dict_s = add_sequences(s, ls, u, v, type, node_vocabs)
        if dict_s is not None:
            s, s1, ls_1 = dict_s['s'], dict_s['s1'], dict_s['ls_1']
            all_s += (s + ' ' + s1)
            if len(s1) > 0:
                # The length exceeds 512; if the preceding sequence has not appeared before, add it directly and reset the variables.
                if all_s not in string_set:
                    string_set.add(all_s.strip())
                sequences_now.append(s.strip())
                s = s1
                ls = ls_1
        i += 1
        if len_events == 1:
            # The event length is 1.
            if len(word_sequence_key) > 0:
                if len(s) > 0:
                    sequences_now.append(s)
                if len(s1) > 0:
                    sequences_now.append(s1)

                word_sequences.append(word_sequence_key)
                all_word_sequences.append(all_s.strip())
            else:
                print('ERROR : *********key = ', key, ', : len(word_sequence_key) == 0 *********')
                break
            continue
        # The event length is greater than 1.
        while i < len_events:
            u1, v1, type1, time1 = events[i - 1][0], events[i - 1][1], events[i - 1][3]['type'], events[i - 1][3][
                'start_time']
            u2, v2, type2, time2 = events[i][0], events[i][1], events[i][3]['type'], events[i][3]['start_time']
            time1 = float(time1)
            time2 = float(time2)
            if time1 > time2:
                print('ERROR : *********key = ', key, ', 不是升序的*********')
                break
            if time2 - time1 < max_time_sequence:
                # The interval is below max_time_sequence, so the event can be added.
                dict_s = add_sequences(s, ls, u2, v2, type2, node_vocabs)
                if dict_s is not None:
                    s, s1, ls_1 = dict_s['s'], dict_s['s1'], dict_s['ls_1']
                    all_s += (s + ' ' + s1)
                    if len(s1) > 0:
                        # The length exceeds 512; if the preceding sequence has not appeared before, add it directly and reset the variables.
                        if all_s not in string_set:
                            string_set.add(all_s.strip())
                            word_sequence_key.append(s)
                        s = s1
                        ls = ls_1
                else:
                    print('ERROR : *********key = ', key, ', : dict_s  None *********')
                    break
            else:
                # The interval exceeds max_time_sequence; add the preceding sequence and create a new one for subsequent events.
                # The length exceeds 512; if the preceding sequence has not appeared before, add it directly and reset the variables.
                if all_s not in string_set:
                    string_set.add(all_s)
                    word_sequence_key.append(s)
                    if len(s1) > 0:
                        word_sequence_key.append(s1)
                    word_sequences.append(word_sequence_key)
                    all_word_sequences.append(all_s)
                all_s = ''
                word_sequence_key = []
                s, ls, s1, ls_1 = '', [], '', []
                dict_s = add_sequences(s, ls, u2, v2, type2, node_vocabs)
                if dict_s is not None:
                    s, s1, ls_1 = dict_s['s'], dict_s['s1'], dict_s['ls_1']
            i += 1
        if len(all_s) > 0 and len(word_sequence_key) > 0 and all_s not in string_set:
            word_sequences.append(word_sequence_key)
            all_word_sequences.append(all_s)
    print('len(word_sequences) = ', len(word_sequences), ', len(all_word_sequences) = ', len(all_word_sequences))
    return word_sequences, all_word_sequences


'''
    Find ground-truth sequences.
'''


def find_gt_normal_sequences(attack_events, all_sequences, max_time_sequence=10000):
    """
    Add ground-truth events to normal process-centered sequences to obtain ground-truth sequence statements.
    :param attack_events: Attack events [e1, e2, ...].
    :param all_sequences: All normal process-centered sequences: {key1: [e1, e2, ...]}.
    :param max_time_sequence: Maximum interval between sequence events.
    :return: gt_sequences: Process-centered sequences corresponding to attack events; gt_set: set of sequence statements.
    """
    gt_sequences = {}
    normal_sequences = {}
    for event in attack_events:
        u, v, key, time = event[0], event[1], event[2], float(event[3]['start_time'])
        if u in all_sequences.keys():
            if u not in gt_sequences.keys():
                events = all_sequences[u].copy()
                normal_sequences[u] = all_sequences[u]
                events.append(event)
                gt_sequences[u] = events
            else:
                gt_sequences[u].append(event)
        if v in all_sequences.keys():
            if v not in gt_sequences.keys():
                events = all_sequences[v].copy()
                normal_sequences[v] = all_sequences[v]
                events.append(event)
                gt_sequences[v] = events
            else:
                gt_sequences[v].append(event)
    for key, value in gt_sequences.items():
        ls = sorted(value, key=lambda x: x[3]['start_time'])
        gt_sequences[key] = ls
    return gt_sequences, normal_sequences

def get_gt_process(normal_process_dict, gt_process_dict):
    """
        Obtain ground-truth sequence statements from normal sequence statements.
    :param _type_ normal_process_dict: _description_
    :param _type_ gt_process_dict: _description_
    :return _type_: _description_
    """
    set_word_seqs = set()
    seqs_process_dict = {}
    # Process normal sequence statements.
    for key, value in normal_process_dict.items():
        for seqs in value:
            tuple_seqs = tuple(seqs)
            set_word_seqs.add(tuple_seqs)
    # Process the ground truth.
    for key, value in gt_process_dict.items():
        p_ls = []
        for seqs in value:
            tuple_seqs = tuple(seqs)
            if tuple_seqs not in set_word_seqs:
                p_ls.append(seqs)
        if len(p_ls) > 0:
            seqs_process_dict[key] = p_ls
    return seqs_process_dict
