import numpy as np

from keras import Model, Input
from keras.layers import Resizing

from keras.applications import resnet50, vgg16


INPUT_SHAPE = (32, 32, 3)