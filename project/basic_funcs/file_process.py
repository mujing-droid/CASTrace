#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import numpy as np
import json
import queue
import threading
import time
from sklearn.model_selection import train_test_split

def rename_file(current_file_path, new_file_path):
    # Rename the file.
    try:
        os.rename(current_file_path, new_file_path)
        print(f"Renamed file from {current_file_path} to {new_file_path}.")
    except OSError as e:
        print(f"Failed to rename file. Error: {e}")

def rename_files(file_paths, new_file_paths):
    """Rename files in batches.

    :param _type_ file_paths: File paths.
    :param _type_ new_file_paths: New paths.
    """
    for current_file_path, new_file_path in zip(file_paths, new_file_paths):
        rename_file(current_file_path, new_file_path)

def remove_file(file_path):
    # Delete the file.
    try:
        os.remove(file_path)
        print(f"Deleted file {file_path}.")
    except OSError as e:
        print(f"Failed to delete file {file_path}. Error: {e}")
        
def remove_files(file_paths):
    for file_path in file_paths:
        remove_file(file_path)

def is_file_exist(file_name):
    if os.path.isfile(file_name):
        print(f"File '{file_name}' exists.")
    else:
        print(f"File '{file_name}' does not exist.----------")


def is_all_file_exist(ans_path, file_name_dicts):
    # ans_path = 'output/answers/'
    for key, value in file_name_dicts.items():
        data_path= ans_path + key + '/'
        for key1, value1 in value.items():
            for i in value1:
                path1 = data_path + i
                is_file_exist(path1)



def save_2_npy(data, file_name):
    """Save an NPY file.

    :param _type_ data: Data.
    :param _type_ file_name: Full path.
    """
    file_path = os.path.dirname(file_name)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    # Save to a NumPy binary .npy file.
    np.save(file_name, data)


def read_npy_file(file_name, result_queue=None):
    two_dimensional_array = np.load(file_name)
    if result_queue is not None:
        result_queue.put(two_dimensional_array)
    return two_dimensional_array    


def split_big_2_small(big_data, split_num=2):
    """Split a large NumPy array into smaller arrays.

    :param numpy.ndarray big_data: _description_
    :param int split_num: _description_, defaults to 2
    :return list: [numpy.ndarray, numpy.ndarray, ...]
    """
    # Split the array evenly with numpy.array_split.
    split_arrays_even = np.array_split(big_data, split_num)
    return split_arrays_even
    

def read_npy_multithread(path, file_names):
    """
        Read multiple JSON files using multiple threads.
    :param path: Path.
    :param file_names: List of file names.
    :return: ls : [ [], []]
    """
    # Get the thread count.
    thread_nums = len(file_names)
    threads = []
    ans_ls = []
    # thread_file_names = []
    # start_time = time.time()
    for i in range(thread_nums):
        file_path = path + file_names[i]
        result_queue = queue.Queue()
        thread = threading.Thread(target=read_npy_file,
                                  args=(file_path, result_queue))
        threads.append(thread)
        thread.start()
        ans_ls.append(result_queue)
        # thread_file_names.append(file_names[i])
    # Wait for all threads to finish.
    for thread in threads:
        thread.join()
    # end_time = time.time()
    # print(f'multi thread read files : {end_time - start_time:.8f}s')

    ls = []
    for j in ans_ls:
        # Collect all results.
        while not j.empty():
            ls1 = j.get()
            ls.append(ls1)
    return ls


def save_general_ls(ls, file_path, file_name):
    """General-purpose save operation that writes one line at a time in ls order.
    
    :param ls: [ ..., ..., ...]
    :param file_path: Output path, ending with '/'.
    :param file_name: Output file name with an extension, usually .txt.
    :return: None
    """
    if not os.path.exists(file_path):
        os.makedirs(file_path)
        # print(file_path + "Folder created")
    # else:
        # print(file_path + "Folder already exists")
    with open(file_path + file_name, 'w', encoding='utf-8') as file:
        for i in ls:
            file.write(str(i) + '\n')


def read_general_ls(file_path, need_eval=True, result_queue=None):
    """
        General-purpose read operation that reads and evaluates each line in file order.
    :param file_path: Path and name of the saved file.
    :return: ls: [ ..., ..., ... ]
    """
    ls = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if need_eval:
                ls.append(eval(line.strip()))
            else:
                ls.append(line.strip())
    if result_queue is not None:
        result_queue.put(ls)
    return ls


def read_general_ls_multithread(path, file_names):
    """
        Read multiple JSON files using multiple threads.
    :param path: Path.
    :param file_names: List of file names.
    :return: ls : [ [], []]
    """
    # Get the thread count.
    thread_nums = len(file_names)
    threads = []
    ans_ls = []
    # thread_file_names = []
    # start_time = time.time()
    for i in range(thread_nums):
        file_path = path + file_names[i]
        result_queue = queue.Queue()
        thread = threading.Thread(target=read_general_ls,
                                  args=(file_path, True, result_queue))
        threads.append(thread)
        thread.start()
        ans_ls.append(result_queue)
        # thread_file_names.append(file_names[i])
    # Wait for all threads to finish.
    for thread in threads:
        thread.join()
    # end_time = time.time()
    # print(f'multi thread read files : {end_time - start_time:.8f}s')

    ls = []
    for j in ans_ls:
        # Collect all results.
        while not j.empty():
            ls1 = j.get()
            ls.append(ls1)
    return ls


def save_general_dict(dict, file_path, file_name):
    """
    Save a dictionary.
    :param dict:
    :param file_path:
    :param file_name:
    :return: None
    """
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    with open(file_path + file_name, "w", encoding='utf-8') as file:
        for key, value in dict.items():
            # print('key = ', key, ', value = ', value)
            file.write(key + '--fenge--' + str(value) + '\n')


def read_general_dict(file_path):
    """
    Read a dictionary.
    :param file_path:
    :return: Sequence dictionary.
    """
    dict = {}
    with open(file_path, "r", encoding='utf-8') as file:
        for line in file.readlines():
            x = line.strip().split('--fenge--')
            key = x[0]
            value = eval(x[1])
            # key, value = line.split('--fenge--')[0], eval(line.split('--fenge--')[1])
            dict[key] = value
    # print('key = ', key, ', value = ', value[0])
    return dict


def save_dict_json(dict, file_path, file_name):
    """Save a dictionary as a JSON file.

    :param dict dict: _description_
    :param str file_path: Path ending with '/'.
    :param str file_name: File name ending with .json.
    """
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    with open(file_path + file_name, 'w', encoding='utf-8') as json_file:
        json.dump(dict, json_file)


def read_dict_json(file_path, result_queue=None):
    with open(file_path, 'r', encoding='utf-8') as json_file:
        ans = json.load(json_file)
        if result_queue is not None:
            result_queue.put(ans)
        return ans


def read_dict_json_multithread(path, file_names):
    """
        Read multiple JSON files using multiple threads.
    :param path: Path.
    :param file_names: List of file names.
    :return: ls : [ {process - sequences}, {...}, ... ]
    """
    # Get the thread count.
    thread_nums = len(file_names)
    threads = []
    ans_ls = []
    thread_file_names = []
    # start_time = time.time()
    for i in range(thread_nums):
        file_path = path + file_names[i]
        result_queue = queue.Queue()
        thread = threading.Thread(target=read_dict_json,
                                  args=(file_path, result_queue))
        threads.append(thread)
        thread.start()
        ans_ls.append(result_queue)
        thread_file_names.append(file_names[i])
    # Wait for all threads to finish.
    for thread in threads:
        thread.join()
    # end_time = time.time()
    # print(f'multi thread read files : {end_time - start_time:.8f}s')

    ls = []
    for j in ans_ls:
        # Collect all results.
        while not j.empty():
            ls1 = j.get()
            ls.append(ls1)
    # This mainly verifies whether file names retain their insertion order from the for loop, which they should.
    print('------thread_file_names------')
    for i in thread_file_names:
        print(i)
    return ls


"""
    vocabs process
"""


def save_vocabs_dict(node_vocabs, file_name):
    """
    Save a process-to-tokens dictionary: process -> tokens[s1, s2, s3, ...].
    :param node_vocabs: process-tokens
    :param file_name: Output file name.
    :return: None
    """
    with open(file_name, 'w', encoding='utf-8') as file:
        for key, value in node_vocabs.items():
            file.write(str(key) + '--fenge--' + str(value) + '\n')


def read_vocabs_dict(file_name):
    """
    Read a process-to-tokens dictionary.
    :param file_name:
    :return: node_vocabs
    """
    node_vocabs = {}
    with open(file_name, 'r', encoding='utf-8') as file:
        for line in file:
            x = line.strip().split('--fenge--')
            key = x[0]
            value = eval(x[1])
            node_vocabs[key] = value
    return node_vocabs


def read_vocabs_dict_multithread(file_name, result_queue):
    """
    Read dictionaries using multiple threads.
    :param file_name: File name.
    :param result_queue: Queue for return values.
    :return: None
    """
    node_vocabs = {}
    with open(file_name, 'r', encoding='utf-8') as file:
        for line in file:
            x = line.strip().split('--fenge--')
            key = x[0]
            value = eval(x[1])
            node_vocabs[key] = value
    # return node_vocabs
    result_queue.put(node_vocabs)


'''
    word sequences process
'''


def ls_tow_2_string(ls):
    """
    Convert inner lists in a two-dimensional list to strings; this may be unnecessary.
    :param ls: Two-dimensional list: [['s1', 's2', ...], [], ...].
    :return: ls1
    """
    ls1 = []
    len_i = 0
    for i in ls:
        s = '['
        for j in i:
            s += (str(j) + ', ')
        s += ']'
        ls1.append(s)
    return ls1


def save_process_sequences(process_seq_ls, file_name):
    """
    Save sequences grouped by process.
    :param process_seq_ls: [[sequences for process 1], [sequences for process 2], ...].
    :param file_name:
    :return:
    """
    with open(file_name, 'w', encoding='utf-8') as file:
        ls1 = ls_tow_2_string(process_seq_ls)
        # print(len(ls1))
        for i in ls1:
            file.write(i + '\n')


def read_process_sequences(file_name):
    """
    Read a file saved by save_process_sequences.
    :param file_name:
    :return: process_seq_ls
    """
    process_seq_ls = []
    with open(file_name, 'r', encoding='utf-8') as file:
        for line in file:
            process_seq_ls.append(eval(line.strip()))
    return process_seq_ls


def save_process_sequences_multifiles(process_seq_dict, file_path, file_name, max_length=100000):
    """
    Save sequences across multiple files based on the sequence count.
    :param process_seq_dict: Sequences.
    :param file_path: Output path, e.g. 'data/'.
    :param file_name: File name, e.g. 'data1'.
    :param max_length: Maximum number of sequences; split when this limit is exceeded.
    :return: file_paths: List of output paths.
    """
    file_name_first = 'seqs-break-process-'
    ls_breaks, dict_break = [], {}
    index_ls = []
    index_break_ls = []
    # len_all, len_j = 0, 0
    len_dict_break = 0
    len_all = 0
    len_dict_break_ls = []
    # for key, value in process_seq_dict.items():
    #     for i in value:
    #         len_all += len(i)
    #         len_dict_break += len(i)
    #     dict_break[key] = value
    #     if len_dict_break > max_length:
    #         len_dict_break_ls.append(len_dict_break)
    #         len_dict_break = 0
    #         ls_breaks.append(dict_break)
    #         dict_break = {}
    for key, value in process_seq_dict.items():
        index_ls1 = []
        ls1 = []
        len_all_key = 0
        for i in range(len(value)):
            value1 = value[i]
            ls2 = []
            for j in range(len(value1)):
                value2 = value1[j]
                len_dict_break += 1
                if len_dict_break < max_length:
                    index_ls.append((key, i, j))
                    ls2.append(value2)
                if len_dict_break >= max_length:
                    len_dict_break_ls.append(len_dict_break)
                    ls1.append(ls2)
                    index_ls.append((key, i, j))
                    dict_break[key] = ls1
                    index_break_ls.append(index_ls)
                    index_ls = []
                    ls1, ls2 = [], [value2]
                    len_dict_break = 0
                    ls_breaks.append(dict_break)
                    dict_break = {}
            len_all += len(value1)
            # len_dict_break += len(i)
        if len_dict_break < max_length:
            dict_break[key] = value
        if len_dict_break >= max_length:
            len_dict_break_ls.append(len_dict_break)
            len_dict_break = 0
            ls_breaks.append(dict_break)
            dict_break = {}
    if len_dict_break > 0:
        len_dict_break_ls.append(len_dict_break)
        ls_breaks.append(dict_break)
        index_break_ls.append(index_ls)
    file_paths_json = []
    # file_paths_txt = []
    print('len(ls_breaks) = ', len(ls_breaks), ', len_all = ', len_all)
    for i in range(len(ls_breaks)):
        # file_name_new_txt = file_name_first + file_name + '-' + str(i) + '-' + str(len_dict_break_ls[i]) + '.txt'
        file_first_name = file_name_first + file_name + '_' + str(i) + '_' + str(len_dict_break_ls[i])
        file_name_new_json = file_first_name + '.json'
        save_dict_json(ls_breaks[i], file_path, file_name_new_json)
        # save_general_dict(ls_breaks[i], file_path, file_name_new_txt)
        index_file_first_name = file_first_name + '_index.txt'
        
        save_general_ls(index_break_ls[i], file_path, index_file_first_name)
        
        file_paths_json.append(file_name_new_json)
        # file_paths_txt.append(file_name_new_txt)
    return file_paths_json, ls_breaks, index_break_ls #, file_paths_txt



def save_process_sequences_break(process_seq_ls, path, file_name, file_type, max_length=100000):
    """
    Save sequences across multiple files based on the sequence count.
    :param process_seq_ls: Sequences.
    :param path: Output path, e.g. 'data/'.
    :param file_name: File name, e.g. 'data1'.
    :param file_type: File extension, e.g. '.txt'.
    :param max_length: Maximum number of sequences; split when this limit is exceeded.
    :return: file_paths: List of output paths.
    """
    file_name_first = 'seqs-break-process-'
    ls_breaks, ls_break = [], []
    # len_all, len_j = 0, 0
    len_break = 0
    len_all = 0
    for i in process_seq_ls:
        for j in i:
            len_all += len(j)
            len_break += len(j)
        ls_break.append(i)
        if len_break > max_length:
            len_break = 0
            ls_breaks.append(ls_break)
            ls_break = []
    if len_break > 0:
        ls_breaks.append(ls_break)
    file_paths = []
    print('len(ls_breaks) = ', len(ls_breaks), ', len_all = ', len_all)
    for i in range(len(ls_breaks)):
        file_path = path + file_name_first + file_name + '-' + str(i) + file_type
        save_process_sequences(ls_breaks[i], file_path)
        file_paths.append(file_path)
    return file_paths


def read_multi_process_seqs(file_names):
    """
    Read multiple files whose contents are grouped by process.
    :param file_names: File paths and names.
    :return: seq_breaks: [[sequence list from file 1], [from file 2], ...].
    """
    seq_breaks = []
    for i in file_names:
        break_sequences = []
        seqs = read_process_sequences(i)
        for seq_p in seqs:
            for seq in seq_p:
                break_sequences.append(seq)
        seq_breaks.append(break_sequences)
    return seq_breaks


def read_process_sequences_multithread(file_name, result_queue):
    """
    Read files using multiple processes.
    :param file_name:
    :param result_queue:
    :return:
    """
    process_seq_ls = []
    with open(file_name, 'r', encoding='utf-8') as file:
        for line in file:
            process_seq_ls.append(eval(line.strip()))
    result_queue.put(process_seq_ls)
    # return process_seq_ls


def read_seqs_break(file_names, output_path):
    """Read all seqs-break files.

    :param _type_ file_names: _description_
    :param _type_ output_path: _description_
    :return _type_: _description_
    """
    seq_breaks = []
    for i in file_names:
        seqs = read_dict_json(output_path + i)
        seq_breaks.append(seqs)
    return seq_breaks


'''
    Embedding-vector processing.
'''

def numpy2string(n_array):
    """
    Convert a one-dimensional NumPy array to a single-line string.
    :param n_array: One-dimensional array with shape (768,).
    :return: String.
    """
    s = ''
    if type(n_array) == np.ndarray:
        s += '['
        # print(' shape = ', i1.shape)
        for i in n_array:
            s += str(i) + ', '
        s += ']'
    else:
        print('The provided value is not a NumPy array.')
    return s


def save_embeddings(ans_ls, file_path, file_name):
    """
    Save embedding vectors.
    :param ans_ls: Embedding results.
    :param file_path:
    :param file_name:
    :return: None
    """
    # embeddings [ [(1, 768)]  ]
    # print('len(ans_ls) = ', len(ans_ls))
    ls = []
    for i in ans_ls:
        s = ''
        if type(i) == np.ndarray:
            s = numpy2string(i)
        else:
            print('The embedding vectors do not have the expected structure: [numpy.ndarray, ...].')
        ls.append(s)
    save_general_ls(ls, file_path, file_name)


def save_multi_embeddings(embeddings_ls, output_path, embeddings_index_ls):
    embeddings_file_name_ls = []
    embeddings_index_file_name_ls = []
    for i in range(len(embeddings_ls)):
        embeddings = embeddings_ls[i]
        if type(embeddings_ls[i]) == list and type(embeddings_ls[i][0]) == np.ndarray:
            embeddings = np.vstack(embeddings_ls[i])
        embeddings_file_name = 'embeddings_normal-' + str(i) + '.npy'
        save_2_npy(embeddings, output_path + embeddings_file_name)
        embeddings_index_file_name = 'embeddings_normal_index-' + str(i) + '.npy'
        save_general_ls(embeddings_index_ls[i], output_path, embeddings_index_file_name)
        embeddings_file_name_ls.append(embeddings_file_name)
        embeddings_index_file_name_ls.append(embeddings_index_file_name)
    # file_name_dict = {
    #     'embeddings_file_name': embeddings_file_name,
    #     'embeddings_index_file_name': embeddings_index_file_name,
    # }
    return embeddings_file_name_ls, embeddings_index_file_name_ls
"""
Large-data processing.
"""


def split_save_train_data(file_name, output_path, save_path, data_names, test_size):
    """Split the training dataset.

    :param str file_name: Name of the data being processed.
    :param list data_names: List of names for all embedded data.
    :param int test_size: Test-set proportion.
    :return file_name_dict: List of file names.
            file_name_dict = {
                'X_train_file_name': [],
                'X_test_file_name': [],
                'X_train_index_file_name': [],
                'X_test_index_file_name': []
            }
    """
    # save_path = ans_path + file_name + '/'
    file_name_dict = {
        'X_train_file_name': [],
        'X_test_file_name': [],
        'X_train_index_file_name': [],
        'X_test_index_file_name': []
    }
    for ii in range(len(data_names)):
        data_name = data_names[ii]
        print(f'----------start split {data_name}----------')
        
        start_time = time.time()
        embeddings_normal = read_npy_file(output_path + data_name)
        print(f'embeddings_normal.shape : {embeddings_normal.shape}')
        end_time = time.time()
        read_time = f'{end_time - start_time: .6f}'
        print(f'\tread_npy_file : {read_time}s')
        
        
        len_normal = len(embeddings_normal)
        
        
        # data_index = [i for i in range(len_normal)]
        data_index = np.arange(len_normal)
        # y = np.ones(len_normal)
        start_time = time.time()
        X_train_index, X_test_index = train_test_split(data_index, test_size=test_size,
                                                                random_state=42)
        # , y_normal_train, y_normal_test 
        end_time = time.time()
        # X_train = [embeddings_normal[i] for i in X_train_index]
        # X_test = [embeddings_normal[i] for i in X_test_index]
        
        X_train = embeddings_normal[X_train_index]
        X_test = embeddings_normal[X_test_index]
        print(f'X_train.shape : {X_train.shape}, X_test.shape : {X_test.shape}, X_train_index.shape : {X_train_index.shape}, X_test_index.shape : {X_test_index.shape}')
        train_test_split_time = f'{end_time - start_time: .6f}'
        print(f'\ttrain_test_split_time : {train_test_split_time}s')
        
        # X_train = np.array(X_train)
        # X_test = np.array(X_test)
        # X_train_index = np.array(X_train_index, dtype=np.int32)
        # X_test_index = np.array(X_test_index, dtype=np.int32)
        # y_normal_train = np.array(y_normal_train)
        # y_normal_test = np.array(y_normal_test)
        
        X_train_file_name = 'X_train-' + str(ii) + '.npy'
        X_test_file_name = 'X_test-' + str(ii) + '.npy'
        X_train_index_file_name = 'X_train_index-' + str(ii) + '.npy'
        X_test_index_file_name = 'X_test_index-' + str(ii) + '.npy'
        
        file_name_dict['X_train_file_name'].append(X_train_file_name)
        file_name_dict['X_test_file_name'].append(X_test_file_name)
        file_name_dict['X_train_index_file_name'].append(X_train_index_file_name)
        file_name_dict['X_test_index_file_name'].append(X_test_index_file_name)
        
        print(f'{X_train_file_name}, {X_test_file_name}, {X_train_index_file_name}, {X_test_index_file_name}')
        
        start_time = time.time()
        save_2_npy(X_train, save_path + X_train_file_name)
        end_time = time.time()
        save_time = f'{end_time - start_time: .6f}'
        print(f'\tsave X_train 2_npy time : {save_time}s')
        
        start_time = time.time()
        save_2_npy(X_test, save_path + X_test_file_name)
        end_time = time.time()
        save_time = f'{end_time - start_time: .6f}'
        print(f'\tsave X_test 2_npy time : {save_time}s')
        
        save_2_npy(X_train_index, save_path + X_train_index_file_name)
        save_2_npy(X_test_index, save_path + X_test_index_file_name)
        print(f'---------- split {file_name} OK ----------\n\n')
    
    for k, v in file_name_dict.items():
        print(f"'{k}' : {str(v)}")
    return file_name_dict
