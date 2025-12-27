#!/bin/bash
# Script to download data from Google Drive link and save to data directory

# Google Drive file ID and destination
FILE_ID="1YZQFSonulXuagMIfbJkZeTFJ6qEUuUxL"
DEST_DIR="$(dirname "$0")/.."
DEST_FILE="$DEST_DIR/data_downloaded.zip"

# Download using gdown (recommended for Google Drive large files)
if ! command -v gdown &> /dev/null; then
    echo "gdown not found. Installing via pip..."
    pip install gdown || { echo "Failed to install gdown"; exit 1; }
fi

echo "Downloading file from Google Drive..."
gdown --id "$FILE_ID" -O "$DEST_FILE"

if [ $? -eq 0 ]; then
    echo "Download completed: $DEST_FILE"
else
    echo "Download failed."
    exit 1
fi
