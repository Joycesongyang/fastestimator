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

from typing import Any, Callable, Dict, Iterable, List, Union

import numpy as np

from fastestimator.op.numpyop import NumpyOp


class Binarize(NumpyOp):
    """ Binarize the input data such that all elemements not less than threshold become 1 otherwise 0.

    Args:
        threshold: Binarize threshold.
        inputs: Input key(s) of data to be binarized
        outputs: Output key(s) of binarized data
        mode: What execution mode (train, eval, None) to apply this operation
    """

    def __init__(self,
                 threshold: float,
                 inputs: Union[None, str, Iterable[str], Callable] = None,
                 outputs: Union[None, str, Iterable[str]] = None,
                 mode: Union[None, str, Iterable[str]] = None):

        super().__init__(inputs=inputs, outputs=outputs, mode=mode)
        self.threshold = threshold
        self.in_list, self.out_list = True, True


    def forward(self, data: List[np.ndarray], state: Dict[str, Any]) -> List[np.ndarray]:
        return [(dat >= self.threshold).astype(np.float32) for dat in data]
