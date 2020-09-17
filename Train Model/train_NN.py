import warnings
warnings.filterwarnings('ignore',category=FutureWarning)
import glob
import os
import keras
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib import style
import collections
import statistics
from os import path
from sklearn.metrics import accuracy_score
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import Sequential
from keras.layers import Dense, LSTM, Conv1D, Flatten
from keras.optimizers import Adam, SGD, Nadam
from keras import backend as K
from keras import regularizers
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from joblib import Parallel, delayed
from tensorflow.python.util import deprecation
deprecation._PRINT_DEPRECATION_WARNINGS = False

def NN_parallel(combo):
    testing_subject = combo[0]
    window_size = combo[1]
    transition_point = combo[2]
    phase_number = combo[3]
    layer_num = combo[4]
    node_num = combo[5]
    optimizer_value = combo[6]

    fe_dir = "/HDD/hipexo/Inseung/feature extraction data/"

    trial_pool = [1, 2, 3]
    subject_pool = [6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 27 ,28]
    del subject_pool[subject_pool.index(testing_subject)]

    X_train = pd.DataFrame()
    Y_train = pd.DataFrame()
    X_test = pd.DataFrame()
    Y_test = pd.DataFrame()
    gp_train = pd.DataFrame()
    gp_test = pd.DataFrame()
    Y_test_result = []
    Y_pred_result = []

######### concat all the training data ##############
    for trial in trial_pool:
        for subject in subject_pool:
            for mode in ["RA2", "RA3", "RA4", "RA5", "RD2", "RD3", "RD4", "RD5","SA1", "SA2", "SA3", "SA4", "SD1", "SD2", "SD3", "SD4"]:
                for starting_leg in ["R", "L"]:
                    train_path = fe_dir+"AB"+str(subject)+"_"+str(mode)+"_W"+str(window_size)+"_TP"+str(int(transition_point*10))+"_S2_"+str(starting_leg)+str(trial)+".csv"

                    if path.exists(train_path) == 1:
                        for train_read_path in glob.glob(train_path):
                            data = pd.read_csv(train_read_path, header=None)
                            X = data.iloc[:, :-3]
                            Y = data.iloc[:, -1]
                            gp = data.iloc[:,-2]
                            X_train = pd.concat([X_train, X], axis=0, ignore_index=True)
                            Y_train = pd.concat([Y_train, Y], axis=0, ignore_index=True)
                            gp_train = pd.concat([gp_train, gp], axis=0, ignore_index=True)

            train_path = fe_dir+"AB"+str(subject)+"_LG_W"+str(window_size)+"_TP0_S2_R"+str(trial)+".csv"    
            if path.exists(train_path) == 1:
                for train_read_path in glob.glob(train_path):
                    data = pd.read_csv(train_read_path, header=None)
                    X = data.iloc[:, :-3]
                    Y = data.iloc[:, -1]
                    gp = data.iloc[:,-2]
                    X_train = pd.concat([X_train, X], axis=0, ignore_index=True)
                    Y_train = pd.concat([Y_train, Y], axis=0, ignore_index=True)
                    gp_train = pd.concat([gp_train, gp], axis=0, ignore_index=True)

    if phase_number == 1:
######### training/testing the unified model ##############
        for mode in ["RA2", "RA3", "RA4", "RA5", "RD2", "RD3", "RD4", "RD5", "SA1", "SA2", "SA3", "SA4", "SD1", "SD2", "SD3", "SD4"]:
            for starting_leg in ["R", "L"]:   
                for trial in trial_pool: 
                    test_path = fe_dir+"AB"+str(testing_subject)+"_"+str(mode)+"_W"+str(window_size)+"_TP"+str(int(transition_point*10))+"_S2_"+str(starting_leg)+str(trial)+".csv"

                    if path.exists(test_path) == 1:
                        for test_read_path in glob.glob(test_path):
                            data = pd.read_csv(test_read_path, header=None)
                            X = data.iloc[:, :-3]
                            Y = data.iloc[:, -1]
                            X_test = pd.concat([X_test, X], axis=0, ignore_index=True)
                            Y_test = pd.concat([Y_test, Y], axis=0, ignore_index=True)

        for trial in trial_pool:
            train_path = fe_dir+"AB"+str(testing_subject)+"_LG_W"+str(window_size)+"_TP0_S2_R"+str(trial)+".csv"

            if path.exists(test_path) == 1:
                for test_read_path in glob.glob(test_path):
                    data = pd.read_csv(test_read_path, header=None)
                    X = data.iloc[:, :-3]
                    Y = data.iloc[:, -1]
                    X_test = pd.concat([X_test, X], axis=0, ignore_index=True)
                    Y_test = pd.concat([Y_test, Y], axis=0, ignore_index=True)
        del [[gp, gp_train, X, Y]]

        NN_model = Sequential()
        if layer_num == 1:
            NN_model.add(Dense(node_num, activation='relu', input_shape=(X_train.shape[1],)))
            NN_model.add(Dense(5, activation='softmax'))
        else:
            ii = 0
            NN_model.add(Dense(node_num, activation='relu', input_shape=(X_train.shape[1],)))
            while ii < layer_num-1:
                ii = ii + 1
                NN_model.add(Dense(node_num, activation='relu'))
            NN_model.add(Dense(5, activation='softmax'))
        NN_model.compile(optimizer=optimizer_value, loss='sparse_categorical_crossentropy', metrics=['acc'])    
        h = NN_model.fit(X_train, np.ravel(Y_train), epochs=200, batch_size=128, verbose=0, validation_data=(X_test, Y_test),shuffle=True,callbacks=[EarlyStopping(patience=100,restore_best_weights=True)])
        idx = np.argmin(h.history['val_loss'])
        NN_overall_accuracy = h.history['val_acc'][idx]
        del [[X_train, Y_train, X_test, Y_test]]

    else:
######### training/testing the phase dependent model ##############
        for mode in ["RA2", "RA3", "RA4", "RA5", "RD2", "RD3", "RD4", "RD5", "SA1", "SA2", "SA3", "SA4", "SD1", "SD2", "SD3", "SD4"]:
            for starting_leg in ["R", "L"]:   
                for trial in trial_pool: 
                    test_path = fe_dir+"AB"+str(testing_subject)+"_"+str(mode)+"_W"+str(window_size)+"_TP"+str(int(transition_point*10))+"_S2_"+str(starting_leg)+str(trial)+".csv"

                    if path.exists(test_path) == 1:
                        for test_read_path in glob.glob(test_path):
                            data = pd.read_csv(test_read_path, header=None)
                            X = data.iloc[:, :-3]
                            Y = data.iloc[:, -1]
                            gp = data.iloc[:,-2]
                            X_test = pd.concat([X_test, X], axis=0, ignore_index=True)
                            Y_test = pd.concat([Y_test, Y], axis=0, ignore_index=True)
                            gp_test = pd.concat([gp_test, gp], axis=0, ignore_index=True)

        for trial in trial_pool:
            train_path = fe_dir+"AB"+str(testing_subject)+"_LG_W"+str(window_size)+"_TP0_S2_R"+str(trial)+".csv"

            if path.exists(test_path) == 1:
                for test_read_path in glob.glob(test_path):
                    data = pd.read_csv(test_read_path, header=None)
                    X = data.iloc[:, :-3]
                    Y = data.iloc[:, -1]
                    gp = data.iloc[:,-2]
                    X_test = pd.concat([X_test, X], axis=0, ignore_index=True)
                    Y_test = pd.concat([Y_test, Y], axis=0, ignore_index=True)
                    gp_test = pd.concat([gp_test, gp], axis=0, ignore_index=True)
        del [[gp, X, Y]]

        gp_train = gp_train.values
        gp_test = gp_test.values
        gp_train[gp_train == 100] = 99.99
        gp_test[gp_test == 100] = 99.99
        gp_train_idx = []
        gp_test_idx = []
        phase_model = []
        phase_count = np.arange(phase_number)

        for ii in phase_count:
            gp_train_idx.append([jj for jj, phase in enumerate(gp_train) if phase >= 0 + (ii/phase_number)*100 and phase < ((ii+1)/phase_number)*100])
            gp_test_idx.append([jj for jj, phase in enumerate(gp_test) if phase >= 0 + (ii/phase_number)*100 and phase < ((ii+1)/phase_number)*100])

        for ii in phase_count:
            NN_model = Sequential()
            if layer_num == 1:
                NN_model.add(Dense(node_num, activation='relu', input_shape=(X_train.shape[1],)))
                NN_model.add(Dense(5, activation='softmax'))
            else:
                counter = 0
                NN_model.add(Dense(node_num, activation='relu', input_shape=(X_train.shape[1],)))
                while counter < layer_num-1:
                    counter = counter + 1
                    NN_model.add(Dense(node_num, activation='relu'))
                NN_model.add(Dense(5, activation='softmax'))

            NN_model.compile(optimizer=optimizer_value, loss='sparse_categorical_crossentropy', metrics=['acc'])
            NN_model.fit(X_train.values[gp_train_idx[ii]], np.ravel(Y_train.values[gp_train_idx[ii]]), epochs=200, batch_size=128, verbose=0,callbacks=[EarlyStopping(patience=100,restore_best_weights=True)])
            phase_model.append(NN_model)

        for ii in phase_count:
            Y_pred = phase_model[ii].predict_classes(X_test.values[gp_test_idx[ii]])
            Y_pred_result.append(Y_pred)
            Y_test_result.append(np.ravel(Y_test.values[gp_test_idx[ii]]))

        del [[X_train, Y_train, X_test, Y_test, gp_train, gp_test]]

        Y_pred_result = np.concatenate(Y_pred_result).ravel()
        Y_test_result = np.concatenate(Y_test_result).ravel()
        NN_overall_accuracy = accuracy_score(Y_test_result, Y_pred_result)

    print("subject = "+str(testing_subject)+" window size = "+str(window_size)+ " phase number = "+ str(phase_number)+" Accuracy = "+str(NN_overall_accuracy))
    base_path_dir = "/HDD/Inseung/Dropbox (GaTech)/ML/data/sensor_fusion/Result/"
    text_file1 = base_path_dir + "NN_phase.txt"
    msg1 = ' '.join([str(testing_subject),str(window_size),str(transition_point),str(phase_number),str(NN_overall_accuracy),"\n"])
    return text_file1, msg1

run_combos = []
# for testing_subject in [6]:
for testing_subject in [6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 27 ,28]:
    for window_size in [350]:
        for transition_point in [0.2]:
            for phase_number in [1, 2, 3, 4, 5, 6, 7, 8]:
                for layer_num in [3]:
                    for node_num in [20]:
                        for optimizer_value in ['RMSprop']:
                            run_combos.append([testing_subject, window_size, transition_point, phase_number, layer_num, node_num, optimizer_value])

result = Parallel(n_jobs=-1)(delayed(NN_parallel)(combo) for combo in run_combos)
for r in result:
    with open(r[0],"a+") as f:
        f.write(r[1])