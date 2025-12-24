# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from hydra import initialize_config_dir
from hydra.core.global_hydra import GlobalHydra

import os
config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "configs"))
if not GlobalHydra.instance().is_initialized():
    initialize_config_dir(config_dir=config_dir, version_base="1.2")
