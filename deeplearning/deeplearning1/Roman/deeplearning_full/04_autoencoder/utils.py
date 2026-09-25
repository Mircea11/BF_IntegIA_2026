import numpy as np
import matplotlib.pyplot as plt
from skimage.util import random_noise

from keras.datasets import mnist

from itertools import chain, cycle
from typing import Generator, Tuple

def load_mnist_noised(var: float, amount: float) -> Generator[Tuple[np.ndarray, np.ndarray, np.ndarray], None, None]:
    for data in mnist.load_data():
        x_noised = random_noise(data[0], var=var)
        x_noised = random_noise(x_noised, 's&p', amount=amount)
        yield (x_noised, data[0]/255, data[1])

def get_lc(history: dict, metrics: list = None):
    if metrics is None:
        metrics = ['loss']
    else:
        metrics.append('loss')

    for metric in metrics:
        plt.figure(figsize=(18, 7))
        plt.title(f'Learning curve for {metric}')
        plt.plot(history.get(metric), label=metric)
        plt.plot(history.get(f'val_{metric}'), label=f'val_{metric}')
        plt.xlabel('epochs')
        plt.ylabel('loss')
        plt.legend()
        plt.show()

def plot_samples(img: np.ndarray, label: np.ndarray, n: int):
    random_index = np.random.randint(0, img.shape[0], n)

    n_rows = n//4+1
    if n % 4 == 0:
        n_rows = n//4

    plt.figure(figsize=(15, 10))
    for i, idx in enumerate(random_index):
        plt.subplot(n_rows, 4, i+1)
        plt.title(label[idx])
        plt.imshow(img[idx], cmap='gray')
        plt.axis('off')
    plt.tight_layout()
    plt.show()

def plot_ae_results(n_samples: int, x_test: np.ndarray, y_test: np.ndarray, y_pred: np.ndarray):
    samples = chain.from_iterable([(x_test[idx], y_test[idx], y_pred[idx]) for idx in np.random.randint(0, x_test.shape[0], n_samples)])
    plt.figure(figsize=(15, 10))
    for i, (img, title) in enumerate(zip(samples, cycle(('Noised', 'Original', 'Denoised',)))):
        plt.subplot(n_samples, 3, i+1)
        plt.title(title, fontdict={'fontsize': 12})
        plt.imshow(img, cmap='gray')
        plt.axis('off')
    plt.tight_layout()
    plt.show()