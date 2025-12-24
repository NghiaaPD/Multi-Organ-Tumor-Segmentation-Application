#!/bin/bash

SAM2p1_BASE_URL="https://dl.fbaipublicfiles.com/segment_anything_2/092824"
sam2p1_hiera_t_url="${SAM2p1_BASE_URL}/sam2.1_hiera_tiny.pt"
sam2p1_hiera_s_url="${SAM2p1_BASE_URL}/sam2.1_hiera_small.pt"
sam2p1_hiera_b_plus_url="${SAM2p1_BASE_URL}/sam2.1_hiera_base_plus.pt"
sam2p1_hiera_l_url="${SAM2p1_BASE_URL}/sam2.1_hiera_large.pt"


OUTDIR="/mnt/data/coden/Multi-Organ-Tumor-Segmentation-Application/tsm/checkpoints/sam2"
mkdir -p "$OUTDIR"

# echo "Downloading sam2.1_hiera_tiny.pt checkpoint..."
# wget -O "$OUTDIR/sam2.1_hiera_tiny.pt" "$sam2p1_hiera_t_url" || { echo "Failed to download checkpoint from $sam2p1_hiera_t_url"; exit 1; }

echo "Downloading sam2.1_hiera_small.pt checkpoint..."
wget -O "$OUTDIR/sam2.1_hiera_small.pt" "$sam2p1_hiera_s_url" || { echo "Failed to download checkpoint from $sam2p1_hiera_s_url"; exit 1; }

# echo "Downloading sam2.1_hiera_base_plus.pt checkpoint..."
# wget -O "$OUTDIR/sam2.1_hiera_base_plus.pt" "$sam2p1_hiera_b_plus_url" || { echo "Failed to download checkpoint from $sam2p1_hiera_b_plus_url"; exit 1; }

# echo "Downloading sam2.1_hiera_large.pt checkpoint..."
# wget -O "$OUTDIR/sam2.1_hiera_large.pt" "$sam2p1_hiera_l_url" || { echo "Failed to download checkpoint from $sam2p1_hiera_l_url"; exit 1; }

echo "All checkpoints are downloaded successfully."