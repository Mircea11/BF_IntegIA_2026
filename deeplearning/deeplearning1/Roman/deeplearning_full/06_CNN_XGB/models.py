import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from model_enum import BaseModel

from keras import Model, Input
from keras.layers import Resizing, Flatten
from keras.datasets import cifar10

from xgboost import XGBClassifier

from typing import Union
from numpy.typing import ArrayLike


# TODO let user pass his own base model
class XgboostCNN:   
    # TODO ADD reference
    def __init__(self, input_shape: tuple, target_shape: tuple, output_layer: ArrayLike = None,
                 base_model: str = 'VGG16', loss: str = 'mlogloss',
                 trainable: bool = False):
        """
        #TODO add xgboost hyper parameters.
    
        Args:
            input_shape (tuple): shape of the given input. Must be a 3D array/tensor (height, width, channels).
            target_shape (tuple): shape of the input for the resizing. Must be a 2D array/tensor (height, width).
            loss (str, optional): loss to optimize with xgboost model. Defaults to 'mlogloss'.
            output_layer (Union[int, tuple]): index for the output layer. Default to None.
            trainable (bool): wheter to retrain layer from pretrained extractor or not. Default to False.
        """
        self.input_shape = input_shape
        self.target_shape = target_shape
        self.base_model = base_model
        self.loss = loss
        self.output_layer = output_layer
        self.trainable = trainable
        self.h = target_shape[0]
        self.w = target_shape[1]


    def fit(self, x: Union[pd.DataFrame, np.array], y: Union[pd.Series, np.array]) -> 'XgboostCNN':
        """
        Extract input features map and fit the xgboost classifier.

        Args:
            x (Union[pd.DataFrame, np.array]): features.
            y (Union[pd.Series, np.array], optional): target.

        Returns:
            XgboostCNN: fitted model
        """
        self._build_extractor()
        self.xgb = XGBClassifier()
        print('extracting features map')
        f_map, self.fmap_train_ = self._split_fmap(self.extractor.predict(x))
        
        # TODO add progress bar for xgb fitting
        print('Fitting xgb')
        self.xgb.fit(f_map, y)
        self._fitted = True
        return self


    def predict(self, x: np.array) -> np.array:
        """
        Extract input features map and predict

        Args:
            x np.array: features.

        Returns:
            np.array: dense predicted class.
        """
        # TODO Custom error class
        if not hasattr(self, 'fitted'):
            raise ValueError('Model is not fitted yet, call fit method first')

        f_map = self.extractor.predict(x)

        if isinstance(f_map, list):
            self.fmap_test_ = f_map[1:]
            f_map = f_map[0]

        return self.xgb.predict(f_map)


    def _build_extractor(self) -> None:
        """
        build toplesss pretrained resnet50 on imagenet to extract features map.
        """
        model = BaseModel[self.base_model].value.get('base')
        pipeline = BaseModel[self.base_model].value.get('pipeline')

        model = model(include_top=False,
                      input_shape=self.target_shape)

        model.trainable = self.trainable

        if self.output_layer:
            model = self._build_multi_output(model)

        inputs = Input(self.input_shape)
        x = pipeline(inputs)
        x = Resizing(self.h, self.w)(x)

        x = model(x)

        if not self.output_layer:
            x = Flatten()(x)

        outputs = x

        self.extractor = Model(inputs=inputs, outputs=outputs,
                               name='xgboost_resnet50')


    def _build_multi_output(self, model: Model) -> Model:
        inputs = model.input

        # first output to flatten and give to xgb            
        outputs = [model.layers[len(model.layers)-1].output]

        if isinstance(self.output_layer, tuple):
            [outputs.append(model.layers[idx].output) for idx in self.output_layer]
        else:
            outputs.append(model.layers[self.output_layer].output)

        outputs[0] = Flatten()(outputs[0])

        return Model(inputs=inputs, outputs=outputs)

    def _split_fmap(self, fmap: list):
        return (fmap[0], fmap[1:]) if self.output_layer else (fmap[0], None)


def plot_fmaps(x: np.array, fmap: np.array, id: int,  n: int, output_layer: int):
    plt.imshow(x[id])
    plt.show()
    
    idx = np.random.randint(0, fmap[output_layer].shape[3], n)

    plt.figure(figsize=(20, 50))
    for i, map_idx in enumerate(idx):
        plt.subplot(n // 6 + 1, 6, i+1)
        plt.title(map_idx)
        plt.imshow(fmap[output_layer][id, :, :, map_idx], cmap='gray')
    plt.show()


if __name__ == '__main__':
    INPUT_SHAPE = (32, 32, 3)
    target_shape = (50, 50, 3)

    (x_train, y_train), (x_test, y_test) = cifar10.load_data()

    sample = np.random.randint(0, x_train.shape[0], 1000)
    x_train = x_train[sample]
    y_train = y_train[sample]

    model = XgboostCNN(INPUT_SHAPE, target_shape, base_model='RESNET50',
                       output_layer=(7, 12))

    model.fit(x_train, y_train)

