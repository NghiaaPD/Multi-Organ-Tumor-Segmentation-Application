#!/bin/bash
# Distributed training script for FastViT using torch.distributed.launch

# Set variables (edit as needed)
: ${DATASET_DIR:="data/MOTSA_classification"}
: ${OUTPUT_DIR:="./output"}
: ${MODEL:="fastvit_ma36"}
: ${BATCH_SIZE:=4}
: ${LR:=0.001}
: ${NPROC_PER_NODE:=1}
: ${INPUT_SIZE:="3 256 256"}
: ${DROP_PATH:=0.2}


python -m torch.distributed.launch --nproc_per_node=$NPROC_PER_NODE tsm/train/fastvit/train.py \
    "$DATASET_DIR" \
    --model $MODEL \
    -b $BATCH_SIZE \
    --lr $LR \
    --native-amp \
    --output "$OUTPUT_DIR" \
    --input-size $INPUT_SIZE \
    --drop-path $DROP_PATH \
    --num-classes 3 \
    --finetune \
    --resume "tsm/checkpoints/fastvit/fastvit_ma36_reparam.pth.tar"

# End of script