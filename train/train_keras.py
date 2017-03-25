#!/usr/bin/env python

"""
Train a CNN on CIFAR 100.

Takes about 100 minutes.
"""

from __future__ import print_function
import numpy as np
np.random.seed(0)
from keras.preprocessing.image import ImageDataGenerator
from keras import backend as K
from keras.callbacks import ModelCheckpoint
from keras.utils import np_utils
# from sklearn.model_selection import train_test_split
import csv
import os


def main(data_module, model_module, optimizer_module, filename, config):
    """Patch everything together."""
    batch_size = config['train']['batch_size']
    nb_epoch = config['train']['epochs']

    if 'nb_classes' in config['dataset']:
        nb_classes = config['dataset']['nb_classes']
    else:
        nb_classes = data_module.n_classes
    # input image dimensions
    if 'img_rows' in config['dataset']:
        img_rows = config['dataset']['img_rows']
    else:
        img_rows = data_module.img_rows
    if 'img_cols' in config['dataset']:
        img_cols = config['dataset']['img_cols']
    else:
        img_cols = data_module.img_cols
    if 'img_channels' in config['dataset']:
        img_channels = config['dataset']['img_channels']
    else:
        img_channels = data_module.img_channels

    if 'data_augmentation' in config['train']:
        data_augmentation = config['train']['data_augmentation']
    else:
        data_augmentation = True

    # The data, shuffled and split between train and test sets:
    data = data_module.load_data()
    print("Data loaded.")
    X_train, y_train = data['x_train'], data['y_train']
    X_train = data_module.preprocess(X_train)
    X_test, y_test = data['x_test'], data['y_test']
    X_test = data_module.preprocess(X_test)
    # X_train, X_val, y_train, y_val = train_test_split(X_train, y_train,
    #                                                   test_size=0.10,
    #                                                   random_state=42)

    # Convert class vectors to binary class matrices.
    Y_train = np_utils.to_categorical(y_train, nb_classes)
    # Y_train = Y_train.reshape((-1, 1, 1, nb_classes))  # For fcn

    # Y_val = np_utils.to_categorical(y_val, nb_classes)
    Y_test = np_utils.to_categorical(y_test, nb_classes)
    # Y_test = Y_test.reshape((-1, 1, 1, nb_classes))

    # Input shape depends on the backend
    if K.image_dim_ordering() == "th":
        input_shape = (img_channels, img_rows, img_cols)
    else:
        input_shape = (img_rows, img_cols, img_channels)

    model = model_module.create_model(nb_classes, input_shape)
    print("Model created")

    model.summary()
    optimizer = optimizer_module.get_optimizer(config)
    model.compile(loss='categorical_crossentropy',
                  optimizer=optimizer,
                  metrics=["accuracy"])
    print("Finished compiling")
    print("Building model...")

    if not data_augmentation:
        print('Not using data augmentation.')
        model.fit(X_train, Y_train,
                  batch_size=batch_size,
                  epochs=nb_epoch,
                  validation_data=(X_test, Y_test),
                  shuffle=True)
    else:
        print('Using real-time data augmentation.')
        # This will do preprocessing and realtime data augmentation:
        datagen = ImageDataGenerator(
            featurewise_center=False,  # set input mean to 0 over the dataset
            samplewise_center=False,  # set each sample mean to 0
            # divide inputs by std of the dataset
            featurewise_std_normalization=False,
            samplewise_std_normalization=False,  # divide each input by its std
            zca_whitening=False,  # apply ZCA whitening
            # randomly rotate images in the range (degrees, 0 to 180)
            rotation_range=15,
            # randomly shift images horizontally (fraction of total width)
            width_shift_range=5. / 32,
            # randomly shift images vertically (fraction of total height)
            height_shift_range=5. / 32,
            horizontal_flip=True,  # randomly flip images
            vertical_flip=False)  # randomly flip images

        # Compute quantities required for featurewise normalization
        # (std, mean, and principal components if ZCA whitening is applied).
        datagen.fit(X_train, seed=0)

        # Fit the model on the batches generated by datagen.flow().
        model_chk_path = os.path.join(config['train']['artifacts_path'],
                                      config['train']['checkpoint_fname'])
        cb = ModelCheckpoint(model_chk_path,
                             monitor="val_acc",
                             save_best_only=True,
                             save_weights_only=False)
        history_cb = model.fit_generator(datagen.flow(X_train, Y_train,
                                         batch_size=batch_size),
                                         steps_per_epoch=X_train.shape[0],
                                         epochs=nb_epoch,
                                         validation_data=(X_test, Y_test),
                                         callbacks=[cb])
        loss_history = history_cb.history["loss"]
        acc_history = history_cb.history["acc"]
        val_acc_history = history_cb.history["val_acc"]
        np_loss_history = np.array(loss_history)
        np_acc_history = np.array(acc_history)
        np_val_acc_history = np.array(val_acc_history)
        data = zip(np_loss_history, np_acc_history, np_val_acc_history)
        data = [("%0.4f" % el[0],
                 "%0.4f" % el[1],
                 "%0.4f" % el[2]) for el in data]
        with open(config['train']['history_fname'], 'w') as fp:
            writer = csv.writer(fp, delimiter=',')
            writer.writerows([("loss", "acc", "val_acc")])
            writer.writerows(data)
    model_fn = os.path.join(config['train']['artifacts_path'],
                            config['train']['model_output_fname'])
    model.save(model_fn)
