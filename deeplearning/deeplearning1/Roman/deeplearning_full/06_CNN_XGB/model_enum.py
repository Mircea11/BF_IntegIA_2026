from enum import Enum
from keras.applications import (vgg16, vgg19, resnet50, densenet,
                                resnet_v2, efficientnet)


# TODO add some custom models
class BaseModel(Enum):
    VGG16 = {
        'base': vgg16.VGG16,
        'pipeline': vgg16.preprocess_input 
    }

    VGG19 = {
        'base': vgg19.VGG19,
        'pipeline': vgg19.preprocess_input

    }

    RESNET50 = {
        'base': resnet50.ResNet50,
        'pipeline': resnet50.preprocess_input
    }

    DENSENET121 = {
        'base': densenet.DenseNet121,
        'pipeline': densenet.preprocess_input # pass function. no preprocess needed

    }

    RESNET50V2 = {
        'base': resnet_v2.ResNet50V2,
        'pipeline': resnet_v2.preprocess_input
    }

    EFFICIENTNETB7 = {
        'base': efficientnet.EfficientNetB7,
        'pipeline': efficientnet.preprocess_input
    }



if __name__ == '__main__':
    BaseModel