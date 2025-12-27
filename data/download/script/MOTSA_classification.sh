#!/bin/bash
# Script to download MOTSA_classification.sh from Google Drive

if ! command -v gdown &> /dev/null; then
	echo "gdown not found, installing..."
	pip install gdown
fi

echo "Downloading MOTSA_classification.sh from Google Drive..."
gdown --id 1ipd47-FuB06IUV3Ls9i_mf8y5ZaqECHU -O MOTSA_classification.sh
echo "Download complete: MOTSA_classification.sh"
