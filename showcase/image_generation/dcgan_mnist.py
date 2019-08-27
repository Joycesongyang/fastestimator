# Copyright 2019 The FastEstimator Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""DCGAN example using MNIST data set."""
import numpy as np
import tensorflow as tf
from tensorflow.python.keras import layers

from fastestimator.estimator.estimator import Estimator
from fastestimator.network.loss import Loss
from fastestimator.network.model import FEModel, ModelOp
from fastestimator.network.network import Network
from fastestimator.pipeline.pipeline import Pipeline
from fastestimator.util.op import TensorOp


class GLoss(Loss):
    """Compute generator loss."""
    def __init__(self, inputs, outputs=None, mode=None):
        super().__init__(inputs=inputs, outputs=outputs, mode=mode)
        self.cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits=True, reduction=tf.keras.losses.Reduction.NONE)

    def forward(self, data, state):
        return self.cross_entropy(tf.ones_like(data), data)


class DLoss(Loss):
    """Compute discrimator loss."""
    def __init__(self, inputs, outputs=None, mode=None):
        super().__init__(inputs=inputs, outputs=outputs, mode=mode)
        self.cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits=True, reduction=tf.keras.losses.Reduction.NONE)

    def forward(self, data, state):
        true, fake = data
        real_loss = self.cross_entropy(tf.ones_like(true), true)
        fake_loss = self.cross_entropy(tf.zeros_like(fake), fake)
        total_loss = real_loss + fake_loss
        return total_loss


def make_generator_model():
    model = tf.keras.Sequential()
    model.add(layers.Dense(7 * 7 * 256, use_bias=False, input_shape=(100, )))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())
    model.add(layers.Reshape((7, 7, 256)))
    assert model.output_shape == (None, 7, 7, 256)  # Note: None is the batch size
    model.add(layers.Conv2DTranspose(128, (5, 5), strides=(1, 1), padding='same', use_bias=False))
    assert model.output_shape == (None, 7, 7, 128)
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())
    model.add(layers.Conv2DTranspose(64, (5, 5), strides=(2, 2), padding='same', use_bias=False))
    assert model.output_shape == (None, 14, 14, 64)
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())
    model.add(layers.Conv2DTranspose(1, (5, 5), strides=(2, 2), padding='same', use_bias=False, activation='tanh'))
    assert model.output_shape == (None, 28, 28, 1)
    return model


def make_discriminator_model():
    model = tf.keras.Sequential()
    model.add(layers.Conv2D(64, (5, 5), strides=(2, 2), padding='same', input_shape=[28, 28, 1]))
    model.add(layers.LeakyReLU())
    model.add(layers.Dropout(0.3))
    model.add(layers.Conv2D(128, (5, 5), strides=(2, 2), padding='same'))
    model.add(layers.LeakyReLU())
    model.add(layers.Dropout(0.3))
    model.add(layers.Flatten())
    model.add(layers.Dense(1))
    return model


class Myrescale(TensorOp):
    """Scale image values from uint8 to float32 between -1 and 1."""
    def forward(self, data, state):
        data = tf.cast(data, tf.float32)
        data = (data - 127.5) / 127.5
        return data


def get_estimator(batch_size=256, epochs=10):
    # prepare data
    (x_train, _), (x_eval, _) = tf.keras.datasets.mnist.load_data()
    data = {"train": {"x": np.expand_dims(x_train, -1)}, "eval": {"x": np.expand_dims(x_eval, -1)}}
    pipeline = Pipeline(batch_per_device=batch_size, data=data, ops=Myrescale(inputs="x", outputs="x"))
    # prepare model
    g_bundle = FEModel(model_def=make_generator_model, model_name="gen", loss_name="gloss", optimizer=tf.optimizers.Adam(1e-4))
    d_bundle = FEModel(model_def=make_discriminator_model, model_name="disc", loss_name="dloss", optimizer=tf.optimizers.Adam(1e-4))
    network = Network(ops=[
        ModelOp(inputs=lambda: tf.random.normal([batch_size, 100]), bundle=g_bundle),
        ModelOp(bundle=d_bundle, outputs="pred_fake"),
        ModelOp(inputs="x", bundle=d_bundle, outputs="pred_true"),
        GLoss(inputs=("pred_fake"), outputs="gloss"),
        DLoss(inputs=("pred_true", "pred_fake"), outputs="dloss")
    ])
    # prepare estimator
    estimator = Estimator(network=network, pipeline=pipeline, epochs=epochs)
    return estimator
