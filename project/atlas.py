#!/usr/bin/env python3
# -*- encoding: utf-8 -*-


import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Conv1D, MaxPooling1D, Dropout
from sklearn.model_selection import StratifiedKFold
from basic_funcs.tools import *
from basic_funcs.file_process import *
from values import *
import tensorflow as tf
import os
import time
import math
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from keras.preprocessing import sequence
# Set the TensorFlow log level to 2 so that only errors are reported.
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def lstm_train(x_train, y_train, need_kflod=True):
    # Define the LSTM model.
    kernel_size = 5
    filters =  64
    pool_size = 8
    lstm_output_size = 256
    EPOCH = 4
    batch_size = 1
    model = Sequential()
    model.add(Conv1D(filters, kernel_size, activation='relu'))
    model.add(MaxPooling1D(pool_size=pool_size))
    model.add(Dropout(0.2))
    model.add(LSTM(lstm_output_size))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy']) 
    seed = 1337
    np.random.seed(seed)
    if need_kflod:
        cvscores = []
        kfold = StratifiedKFold(n_splits=6, shuffle=True, random_state=seed)
        for train, test in kfold.split(x_train, y_train):
            model.fit(x_train[train], y_train[train], epochs=EPOCH, batch_size=batch_size, verbose=0)
            # evaluate the model
            scores = model.evaluate(x_train[test], y_train[test], verbose=0)
            print("%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))
            cvscores.append(scores[1] * 100)
        print("%.2f%% (+/- %.2f%%)" % (np.mean(cvscores), np.std(cvscores)))
    else:
        model.fit(x_train, y_train, epochs=EPOCH, batch_size=batch_size)
    
    # # Test the model.
    # # Use the first 10 training samples for prediction.
    # test_data = data[:10]
    # predictions = model.predict(test_data)
    # # Print the predictions and ground-truth labels.
    # print("Predictions:", predictions)
    # print("True labels:", labels[:10])
    return model


def over_under_sample(X_noraml, X_abnormal):
    y_normal = np.zeros(len(X_noraml))
    y_abnormal = np.ones(len(X_abnormal))
    X_train = np.concatenate((X_noraml, X_abnormal), axis=0)
    y_train = np.concatenate((y_normal, y_abnormal), axis=0)
    if (len(X_noraml) > len(X_abnormal) * 90):
        rus = RandomUnderSampler(sampling_strategy={0: 99, 1:1}, random_state=42)  # Undersample positive examples to 100 times the negative examples.
        smote = SMOTE(sampling_strategy={1: 1}, random_state=42)  # Oversample negative examples to 100 times the negative examples.
        # Create the pipeline.
        pipeline = Pipeline([
            ('under', rus),
            ('over', smote)
        ])
        # Apply the pipeline to the training data.
        X_resampled, y_resampled = pipeline.fit_resample(X_train, y_train)
        X_train, y_train = X_resampled, y_resampled
    return X_train, y_train


def list_similarity(list1, list2):
    """A simple edit-distance algorithm.

    :return _type_: _description_
    """
    ls1 = list1
    len_list1 = len(list1)
    len_list2 = len(list2)
    if len_list2 > len_list1:
        list1 = list2
        list2 = ls1
        len_list1 = len(list1)
        len_list2 = len(list2)
    total_distance = 0
    for i in range(len_list1):
        if i < len_list2:
            if list1[i] != list2[i]:
                total_distance += 1
        else:
            total_distance += 1
    # Calculate the average edit distance.
    average_distance = 1 - total_distance / len_list1
    return average_distance


def get_similar_list(embeddings_ls):
    """Get the similarity matrix.

    :param _type_ embeddings_ls: _description_
    :return _type_: _description_
    """
    ls = []
    for i in range(len(embeddings_ls)):
        ls1 = []
        for j in range(i, len(embeddings_ls)):
            if i == j:
                ls1.append(1)
                continue
            distance1 = list_similarity(embeddings_ls[i], embeddings_ls[j])
            print(distance1)
            ls1.append(distance1)
        ls.append(ls1)
    return ls


def under_smapling(embeddings_ls, number):
    """Undersample the data.

    :param _type_ embeddings_ls: _description_
    :param _type_ number: Number of samples to remove.
    """
    similarity_ls = get_similar_list(embeddings_ls)
    del_set = set()
    len_set = 0
    for i in range(len(similarity_ls)):
        for j in range(i+1, len(similarity_ls[i])):
            if similarity_ls[i][j] > 0.5:
                del_set.add(j)
                len_set += 1
            if len_set >= number:
                break
        if len_set >= number:
            break
    if len_set < number:
        for i in range(len(similarity_ls)):
            for j in range(i+1, len(similarity_ls[i])):
                if similarity_ls[i][j] > 0.3:
                    del_set.add(j)
                    len_set += 1
                if len_set >= number:
                    break
            if len_set >= number:
                break
    new_embeddings_ls = []
    for i in embeddings_ls:
        if i not in del_set:
            new_embeddings_ls.append(i)
    return new_embeddings_ls
    

def prepare_data(attack_embeddings, nonattack_embeddings):
    # len_attack = len(attack_embeddings)
    # len_nonattack = len(nonattack_embeddings)
    # if len_nonattack > len_attack and len_nonattack / len_attack > 4:
    #     n = len_nonattack - len_attack * 4
    #     nonattack_embeddings = under_smapling(nonattack_embeddings, n)
    x_train = []
    y_train = []
    for i in attack_embeddings:
        x_train.append(i)
        y_train.append(1)
    for i in nonattack_embeddings:
        x_train.append(i)
        y_train.append(0)
    maxlen = 400
    x_train_new = []
    for i in x_train:
        array1 = np.array(i)
        len_i = len(i)
        if len_i < maxlen:
            array1 = np.pad(array1, (0, maxlen-len(i)), mode='constant', constant_values=0)
        elif len_i > maxlen:
            array1 = np.delete(array1, range(400, len_i))
        x_train_new.append(array1)
    flag = False
    for i in x_train_new:
        if len(i) != 400:
            flag = True
    if flag: print('X train 的长度不是400')
    # sequence.pad_sequences(x_train, maxlen=maxlen, padding="post")
    return x_train_new, y_train


def train_split_data(x_train, y_train):
    test_size = 0.4
    X_train, X_test, y_train, y_test = train_test_split(x_train, y_train, test_size=test_size,
                                                               random_state=42)
    return X_train, X_test, y_train, y_test


test_ans_ls = []
time_dict_train = {}
time_dict_test = {}


def get_x_data(graph_name):
    x_train_normal_path = train_data_path + graph_name + '/' + embedding_name_normal
    x_train_normal = read_npy_file(x_train_normal_path)
    # n = x_train_normal.shape[0]
    # x_train_normal = x_train_normal.reshape((n, 32, 24))
    
    x_train_abnormal_path = train_data_path + graph_name + '/' + embedding_name_gt
    x_train_abnormal = read_npy_file(x_train_abnormal_path)
    n1 = x_train_abnormal.shape[0]
    if n1 > 12:
        k1 = math.ceil(n1*0.4)
        ls = generate_random_numbers(n1, k1)
        ls1 = [x_train_abnormal[i] for i in ls]
        x_train_abnormal = np.array(ls1)
        n1 = k1
    # x_train_abnormal = x_train_abnormal.reshape((n1, 32, 24))
    
    # y_train_normal = np.zeros(n)
    # y_train_abnormal = np.ones(n1)
    
    x_train, y_train = over_under_sample(x_train_normal, x_train_abnormal)
    n = x_train.shape[0]
    x_train = x_train.reshape((n, 32, 24))
    return x_train, y_train
    

def test_case(poi_name, model):
    print(f'\n-----test_case {poi_name}-----')
    # print("func_large_case")
    x_test_path = test_data_path + poi_name + '/' + embedding_name_normal
    y_test_path = test_data_path + poi_name + '/' + file_name_labels
    x_test = read_npy_file(x_test_path)
    n = x_test.shape[0]
    x_test = x_test.reshape((n, 32, 24))
    
    y_test = read_general_ls(y_test_path)
    y_test = np.array(y_test)
    start_time = time.time()
    predictions = model.predict(x_test)
    end_time = time.time()
    print(f'testing time: {end_time - start_time:.4f} seconds')
    time_dict_test[poi_name] = end_time - start_time
    abnormal_2_normal = 0
    normal_2_abnormal = 0
    for i in range(len(predictions)):
        if predictions[i][0] >= 0.5:
            if y_test[i] == 1:
                abnormal_2_normal += 1
            # print('%d is normal' % i)
        else:
            if y_test[i] == 0:
                normal_2_abnormal += 1
            # print('%d is abnormal' % i)
    print(f'{poi_name}, abnormal_2_normal: {abnormal_2_normal}, normal_2_abnormal: {normal_2_abnormal}')
    test_ans_ls.append([poi_name, abnormal_2_normal, normal_2_abnormal])
    return abnormal_2_normal, normal_2_abnormal

# def test_small_case(poi_name, model):
#     x_test_path = test_data_path + poi_name + '/' + embedding_name_normal
#     y_test_path = test_data_path + poi_name + '/' + file_name_labels
#     print("func_small_case")

def test_lstm(graph_name):
    print(f'----------test_lstm {graph_name}----------')
    x_train, y_train = get_x_data(graph_name)
    start_time = time.time()
    model = lstm_train(x_train, y_train)
    end_time = time.time()
    print(f'training time: {end_time - start_time:.4f} seconds')
    time_dict_train[graph_name] = end_time - start_time
    model.save(atlas_save_path + f'{graph_name}.h5')
    if graph_name in large_file_names_dict.keys():
        # Iterate when processing large1 through large7.
        # test_large_case(large_file_names_dict[graph_name], model)
        loop_func(test_case, all_poi_names=large_file_names_dict[graph_name], model=model)
    else :
        test_case(graph_name, model)


# if __name__ == '__main__':
#     log_file_name = 'atlas_result'
#     save_log(log_path_atlas, log_file_name)
#     loop_func(test_lstm, all_poi_names=all_graph_names)
#     print('poi_name, abnormal_2_normal, normal_2_abnormal')
#     for ans in test_ans_ls:
#         print(f'{ans[0]} , {ans[1]} , {ans[2]}')
#     print('graph_name, train_time')
#     for k,v in time_dict_train.items():
#         print(f'{k}, {v:.4f}')
#     print('graph_name, test_time')
#     for k,v in time_dict_test.items():
#         print(f'{k}, {v:.4f}')
    
