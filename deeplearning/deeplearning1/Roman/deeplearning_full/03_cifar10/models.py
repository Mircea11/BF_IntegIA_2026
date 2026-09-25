
from keras import Sequential, Model, Input, KerasTensor
from keras.layers import (Rescaling, Flatten, Dense, Convolution2D, MaxPooling2D, BatchNormalization,
                                     RandomZoom, RandomFlip, RandomRotation, Activation, Add, Normalization, GlobalAveragePooling2D)


def get_data_aug() -> None:
    """
    Some data aug to prevent overfitting.
    """
    data_aug = Sequential([RandomRotation(.05),
                           RandomZoom(.05),
                           RandomFlip()])
    return data_aug


def get_simple_model(n_classes: int, optimizer: str = 'adam', kernel_size: int = 3, activation: str = 'relu', padding: str = 'valid') -> Sequential:
    """
    Simple CNN

    Args:
        n_classes (int): number of classes for the output layer.
        optimizer (str, optional): Defaults to 'adam'.
        kernel_size (int, optional): Defaults to 3.
        activation (str, optional): activation function. Defaults to 'relu'.
        padding (str, optional):  Defaults to 'valid'.

    Returns:
        Sequential: compiled model
    """

    model = Sequential([
        Rescaling(1./255),

        get_data_aug(),

        Convolution2D(32, kernel_size, activation=activation, padding=padding),
        BatchNormalization(),
        Convolution2D(32, kernel_size, activation=activation, padding=padding),
        BatchNormalization(),
        MaxPooling2D(2),

        Convolution2D(64, kernel_size, activation=activation, padding=padding),
        BatchNormalization(),
        Convolution2D(64, kernel_size, activation=activation, padding=padding),
        BatchNormalization(),
        MaxPooling2D(2),

        Convolution2D(128, kernel_size, activation=activation, padding=padding),
        BatchNormalization(),
        Convolution2D(128, kernel_size, activation=activation, padding=padding),
        BatchNormalization(),
        MaxPooling2D(2),

        Flatten(),

        Dense(256, activation=activation),
        BatchNormalization(),

        Dense(n_classes, activation='softmax')

    ])

    model.compile(optimizer=optimizer,
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    return model



def identity(x: KerasTensor, filters: int) -> KerasTensor:
    """"
    Identity block for resnet models. Please refers to this paper for more informations:
    https://arxiv.org/abs/1512.03385

    "Identity shortcuts are particularly important for not increasing the complexity of
    the bottleneck architectures that are introduced below." p.6

    Args:
        x (KerasTensor): features.
        filters (int): number of filters for convolution layers.

    Returns:
        x (KerasTensor): processed features.
    """
    skip = x

    x = Convolution2D(filters, 3, padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    x = Convolution2D(filters, 3, padding='same')(x)
    x = BatchNormalization()(x)

    x = Add()([x, skip])
    x = Activation('relu')(x)

    return x


def bottleneck(x: KerasTensor, filters: int) -> KerasTensor:
    """"
    bottleneck block for resnet models. Please refers to this paper for more informations:
    https://arxiv.org/abs/1512.03385

    Args:
        x (KerasTensor): features.
        filters (int): number of filters for convolution layer.

    Returns:
        x (KerasTensor): processed features.
    """
    skip = x
    skip = Convolution2D(filters, 1, strides=2)(skip)
    skip = BatchNormalization()(skip)

    x = Convolution2D(filters, 3, padding='same', strides=2)(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    x = Convolution2D(filters, 3, padding='same')(x)
    x = BatchNormalization()(x)

    x = Add()([x, skip])
    x = Activation('relu')(x)

    return x


def get_resnet34(n_classes: int, input_shape: tuple, optimizer: str = 'adam') -> Model:
    """
    Resnet models. Lot of redundant code for a simpler implementation.
    Please refers to this paper for more informations:
    https://arxiv.org/abs/1512.03385

    Args:
        n_classes (int): number of classes for the output layer.
        input_shape (tuple): (height, width, channels)
        optimizer (str, optional): Defaults to 'adam'.

    Returns:
        Model: compiled resnet model
    """
    inputs = Input(input_shape)

    # start
    x = get_data_aug()(inputs)
    x = Normalization()(x)

    x = Convolution2D(64, 7, padding='same', strides=2)(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling2D(2)(x)

    # first_block
    x = identity(x, 64)
    x = identity(x, 64)
    x = identity(x, 64)

    x = bottleneck(x, 128)

    x = identity(x, 128)
    x = identity(x, 128)
    x = identity(x, 128)

    x = bottleneck(x, 256)

    x = identity(x, 256)
    x = identity(x, 256)
    x = identity(x, 256)
    x = identity(x, 256)
    x = identity(x, 256)

    x = bottleneck(x, 512)

    x = identity(x, 512)
    x = identity(x, 512)

    x = GlobalAveragePooling2D()(x)

    x = Dense(128, activation='relu')(x)

    x = Dense(n_classes, activation='softmax')(x)


    resnet = Model(inputs, x)

    resnet.compile(optimizer=optimizer,
                loss = 'sparse_categorical_crossentropy',
                metrics=['accuracy'])

    return resnet