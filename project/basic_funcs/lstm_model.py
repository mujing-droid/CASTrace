import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Conv1D, MaxPooling1D, Dropout
from sklearn.model_selection import StratifiedKFold

def lstm_train(x_train, y_train, need_kflod):
    # Define the LSTM model.
    kernel_size = 5
    filters =  64
    pool_size = 8
    lstm_output_size = 256
    EPOCH = 8
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


def lstm_predict(model, x_test):
    return model.predict(x_test)
