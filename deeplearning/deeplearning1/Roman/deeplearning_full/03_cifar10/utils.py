import os
from ctypes import Union

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

from torch.utils.tensorboard import SummaryWriter

from keras.callbacks import Callback

from sklearn.metrics import confusion_matrix, classification_report


def make_directories() -> None:
    """
    Create folders for tensorboard.
    """
    if 'logs' not in os.listdir():
        os.mkdir('logs')
    if 'fit' not in os.listdir('logs'):
        os.mkdir('logs/fit')
    if 'models' not in os.listdir():
        os.mkdir('models')


def plot_lc(history: dict, metrics: list|dict = ['loss', 'accuracy']) -> None:
    """
    Plot learning curves for a trained model. By defaults it plots only the loss
    and the accuracy. 

    Args:
        history (dict): history of the trained model
        metrics (list, optional): List or dict with the metrics to plot. Defaults to ['loss', 'accuracy'].
    """
    plt.figure(figsize=(20, 8))
    for i, metric in enumerate(metrics):
        plt.subplot(1, 2, i+1)
        plt.title(f'Learning curve for {metric}\n')
        plt.plot(history[metric], label='train')
        plt.plot(history[f'val_{metric}'], label='val')
        if metric == 'loss':
            plt.ylim((0, 10))
        plt.xlabel('epochs')
        plt.ylabel(metric)
        plt.legend()
    plt.show()


def get_confusion_matrix(y: np.array, y_pred: np.array, classes: list, set_: str, log_dir: str) -> None:
    """
    Create a confusion matrix and transform it in a tensorboard comptible object.

    Args:
        y (np.array): y_true
        y_pred (np.array): predictions
        classes (list): list of the classes. Must be the same order as labels 
        set_ (str): name of the set used to generate the confusion matrix
        log_dir (str): path where to save the cm
    """
    cm = plt.figure(figsize=(10, 5), dpi=150)
    plt.title('Confusion Matrix %s\n' % set_, fontdict={
              'fontsize': 12, 'fontweight': 'bold'})
    sns.heatmap(confusion_matrix(y, y_pred), annot=True, cmap='vlag',
                cbar=False, fmt='d', xticklabels=classes, yticklabels=classes)

    cm_writer = SummaryWriter(log_dir+'/image')
    cm_writer.add_figure('Confusion Matrix %s' % set_, cm, global_step=0)
    cm_writer.close()


def get_classification_report(y: np.array, y_pred: np.array, classes: list, set_: str, log_dir: str) -> None:
    """
    Use sklearn classification report. In order display it in tensorboard:
    1. Get a dictionnary as output of classification_report function
    2. put it in a DataFrame
    3. Reset the index
    4. Export DataFrame to HTML

    Args:
        y (np.array): y_true
        y_pred (np.array): predictions
        classes (list): list of the classes. Must be the same order as labels 
        set_ (str): name of the set used to generate the classification report
        log_dir (str): path where to save the cr
    """
    pd.options.display.float_format = '{:,.2f}'.format
    cr = classification_report(y, y_pred, target_names=classes, output_dict=True)
    cr = pd.DataFrame(cr).T
    cr['support'] = cr['support'].astype(int)

    idx1 = list(cr.index)[:len(cr.index)-3]
    idx2 = list(cr.index)[len(cr.index)-3:]

    [idx1.append(' ') for i in range(3)]
    [idx2.insert(i, ' '*(i+1)) for i in range(len(cr.index)-3)]

    cr = cr.set_index([idx2, idx1])

    writer = SummaryWriter(log_dir+'/classification_report')
    writer.add_text('Classification Report %s' % set_, cr.to_html(), global_step=0)
    writer.close()


def get_reports(y: np.array, y_pred: np.array, classes: list, set_: str, log_dir: str):
    """
    Wrapper that calls get_confusion_matrix and get_classification_report

    Args:
        y (np.array): y_true
        y_pred (np.array): predictions
        classes (list): list of the classes. Must be the same order as labels 
        set_ (str): name of the set used to generate the reports
        log_dir (str): path where to save the cr
    """
    get_confusion_matrix(y, y_pred, classes, set_, log_dir)
    get_classification_report(y, y_pred, classes, set_, log_dir)



class LrFinder(Callback):
    """
    Implementation of LR range test https://arxiv.org/abs/1708.07120 
    The authors suggest to test a range of learning rates values.
    Cfr. p6 for a triangular learning rate range. Authors suggest to use an exponential fucntion to increase or
    decrease de the learning rate.

    Args:
        Callback (Callback): Callback base class from keras.
    """
    # TODO DOCS
    # TODO check implementation, some results might lead to false assumption. Smooth the decay?
    def __init__(self, lr_min: float, lr_max: float, steps: int, scale: str = 'linear'):
        """"

        Args:
            lr_min (float): starting learning rate
            lr_max (float): maximum learning rate
            steps (int): Number of steps. Hig
            scale (str, optional): _description_. Defaults to 'linear'.
        """
        self.lr_min = lr_min
        self.lr_max = lr_max
        self.scale = scale
        self.steps = steps
        self.lr = lr_min

        self.lrs = np.linspace(lr_min, lr_max, steps+1)

    def on_train_begin(self, logs: dict):
        """"
        Setting up variables for the beginning

        Args:
            logs (dict): _description_
        """
        self.step = 0 # Counter for the step
        self.step_loss = [] # List to collect the loss at each step. 
        self.model.optimizer.learning_rate.assign(self.lrs[0])

    def on_train_batch_end(self, batch: int, logs: dict):
        """
        Decay the learning rate.

        Args:
            batch (int): 
            logs (dict):
        """
        self.step += 1
        self.step_loss.append(logs['loss'])
        self.model.optimizer.learning_rate.assign(self.lrs[self.step])

    def on_train_end(self, logs: dict):
        """
        Automatically plot the learning curve at the end of the training.
        # TODO ADD paramter to control this behaviour.

        Args:
            logs (dict): _description_
        """
        self.plot_curve()

    def plot_curve(self):
        """
        Authors suggest:
        "The minimum learning rate can be chosen by dividing the maximum by a factor of 3 or 4." p.3
        
        """
        plt.plot(self.lrs[:-1], self.step_loss)
        plt.xlabel('learning rate')
        plt.xscale(self.scale)
        plt.ylabel('loss')
        plt.ylim(top=6)
        plt.show()
