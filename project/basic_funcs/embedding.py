#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from transformers import BertModel, BertTokenizer
import torch
import math
import numpy
import warnings
import gc
import queue
import threading


def model_set(vocabs, model_file, useGPU=True):
    """
    Configure the model.
    :param model_file:
    :param vocabs: Token vocabulary as a list.
    :param useGPU:
    :return: tokenizer, model
    """
    # vocabs = read_vocab(vocab_file)
    # model_file = 'models/bert-base-uncased'
    tokenizer = BertTokenizer.from_pretrained(model_file, local_files_only=True)
    model = BertModel.from_pretrained(model_file, local_files_only=True)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    tokenizer.add_tokens(vocabs)
    model.resize_token_embeddings(len(tokenizer))

    if useGPU and device == 'cuda':
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Send the model to a GPU if one is available.
        model.to(device)
        # print('device = ', device)
    return tokenizer, model


def embedding_from_ram_gpu_proSeqDict(pro_seq_dict, tokenizer, model, process_name=None, result_queue=None):
    """
    Read truncated sequences from memory and embed them using a GPU.
    :param pro_seq_dict: Dictionary: { 'process': [[s1, s2], [...], ...], ... }.
                e.g.  'ping_6916' : [['ping 6916 clone ping 6916'], ['ping 6916 sendto 128 55 12 67 61082 135 84 161 202 80']]
    :param tokenizer:
    :param model:
    :return:
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ans_ls = []
    embeddings_index = []
    i = 0  # Primarily used to display progress counts.
    for key, value in pro_seq_dict.items():
        # for seq_ls in value:
        for index_value in range(len(value)):
            seq_ls = value[index_value]
            i += 1
            if i % 100 == 0:
                # print('\n' + str(i), end='\t')
                if process_name is not None:
                    print(process_name + ': ' + str(i), end='\t')
                else :
                    print(str(i), end='\t')
            if i % 1000 == 0:
                print()
            # embedding_ls = []
            # for break_sequence in seq_ls:
            for index_word_seq in range(len(seq_ls)):
                break_sequence = seq_ls[index_word_seq]
                break_sequence = break_sequence.strip().lower()
                # encoded_input = tokenizer.encode(break_sequence, return_tensors='pt', padding=True, truncation=True,
                #                                  max_length=512)

                break_sequence = break_sequence.split(' ')
                break_sequence.insert(0, '[CLS]')
                break_sequence.append('[SEP]')
                
                encoded_input = tokenizer.convert_tokens_to_ids(break_sequence)
                encoded_input = torch.tensor([encoded_input])
                encoded_input = encoded_input.to(device)
                
                
                # 4. Get the embedding vector.
                with torch.no_grad():  # Disable gradient calculation to reduce computation.
                    outputs = model(encoded_input)
                # 'outputs.last_hidden_state' contains the final layer's token embeddings.
                word_embeddings = outputs.last_hidden_state
                # 5. Pool the embedding vectors (mean pooling in this example).
                sentence_embedding = torch.mean(word_embeddings, dim=1)
                sentence_embedding = sentence_embedding.cpu()
                embeddings_index.append((key, index_value, index_word_seq))
                sentence_embedding_numpy = sentence_embedding.numpy()  # (1, 768)
                ans_ls.append(sentence_embedding_numpy[0])
    if result_queue is not None:
        dict_ls = {'embeddings': ans_ls, 'index': embeddings_index}
        result_queue.put(dict_ls)
    return ans_ls, embeddings_index


def embedding_from_ram_gpu_eventSeqsDict(event_seqs_dict, tokenizer, model, process_name=None, result_queue=None):
    """
    Read truncated sequences from memory and embed them using a GPU.
    :param event_seqs_dict: Dictionary: { '(u,v,key)': [s1, s2, ...], ... }.
                e.g.  '(ping_6916, ping_6916, 0)' : ['ping 6916 clone ping 6916'], 
                      'ping_6916, 128.55.12.67:61082->135.84.161.202:80' : ['ping 6916 sendto 128 55 12 67 61082 135 84 161 202 80']
    :param tokenizer:
    :param model:
    :return:
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ans_ls = []
    embeddings_index = []
    i = 0  # Primarily used to display progress counts.
    for key, value in event_seqs_dict.items():
        # for seq_ls in value:
        tuple_k = eval(key)
        u1, v1, key1 = tuple_k
        for index_value in range(len(value)):
            break_sequence = value[index_value] # String sequence.
            i += 1
            if i % 100 == 0:
                # print('\n' + str(i), end='\t')
                if process_name is not None:
                    print(process_name + ': ' + str(i), end='\t')
                else :
                    print(str(i), end='\t')
            if i % 1000 == 0:
                print()
            break_sequence = break_sequence.strip().lower()
            # encoded_input = tokenizer.encode(break_sequence, return_tensors='pt', padding=True, truncation=True,
            #                                  max_length=512)
            break_sequence = break_sequence.split(' ')
            break_sequence.insert(0, '[CLS]')
            break_sequence.append('[SEP]')
            
            encoded_input = tokenizer.convert_tokens_to_ids(break_sequence)
            encoded_input = torch.tensor([encoded_input])
            encoded_input = encoded_input.to(device)
            
            # 4. Get the embedding vector.
            with torch.no_grad():  # Disable gradient calculation to reduce computation.
                outputs = model(encoded_input)
            # 'outputs.last_hidden_state' contains the final layer's token embeddings.
            word_embeddings = outputs.last_hidden_state
            # 5. Pool the embedding vectors (mean pooling in this example).
            sentence_embedding = torch.mean(word_embeddings, dim=1)
            sentence_embedding = sentence_embedding.cpu()
            
            embeddings_index.append((u1, v1, key1, index_value))
            sentence_embedding_numpy = sentence_embedding.numpy()  # (1, 768)
            ans_ls.append(sentence_embedding_numpy[0])
    if result_queue is not None:
        dict_ls = {'embeddings': ans_ls, 'index': embeddings_index}
        result_queue.put(dict_ls)
    return ans_ls, embeddings_index


def multithread_embedding(pro_seq_dict_ls, file_names, tokenizer, model):
    """
    Run embedding in multiple processes.
    :param seq_breaks: Process sequences from multiple files: [[sequences from file 1], [from file 2], ...].
    :param file_names: Names of the files; short names are preferable for identifying program progress.
    :param vocabs: Vocabulary [...].
    :param model_file: Location of the pretrained BERT model.
    :return: embeddings_ls: Sequence embeddings for each file.
             time_dict: Elapsed time.
    """
    # Create threads.
    threads = []
    ans_ls = []
    
    thread_num = len(pro_seq_dict_ls)    
    for i in range(thread_num):
        pro_seq_dict = pro_seq_dict_ls[i]
        result_queue = queue.Queue()
        process_name = 'p' + str(i)
        print('\n--------' + process_name + ' process file name : ' + file_names[i] + '--------\n')
        
        thread = threading.Thread(target=embedding_from_ram_gpu_proSeqDict,
                                  args=(pro_seq_dict, tokenizer, model, process_name, result_queue))
        threads.append(thread)
        thread.start()
        ans_ls.append(result_queue)
        
    # Wait for all threads to finish.
    for thread in threads:
        thread.join()

    embeddings_ls = []
    indexs_ls = []
    for i in range(len(ans_ls)):
        file_name = file_names[i]
        # Collect all results.
        j = ans_ls[i]
        while not j.empty():
            dict_ls  = j.get()
            ls = dict_ls['embeddings']
            index_ls = dict_ls['index']
            
            embeddings_ls.append(ls)
            indexs_ls.append(index_ls)
    # print(len(ls))
    # print()
    # for i in embeddings_ls:
    #     print(len(i))
    return embeddings_ls, indexs_ls
