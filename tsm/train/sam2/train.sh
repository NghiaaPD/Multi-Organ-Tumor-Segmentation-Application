#!/bin/bash
# Example usage: ./train.sh <config_path> [additional_args]

set -e

CONFIG_PATH=${1:-configs/sam2.1_training/sam2.1_hiera_b+_MOSE_finetune.yaml}
shift || true

python3 train.py --config "$CONFIG_PATH" "$@"
