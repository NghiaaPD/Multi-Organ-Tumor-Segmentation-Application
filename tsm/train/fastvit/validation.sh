
#!/bin/bash
# Simple wrapper to run validation.py with a checkpoint

DATA_DIR="data/MOTSA_classification"  # <-- Sửa lại đường dẫn này cho đúng bộ dữ liệu validation của bạn
CHECKPOINT="output/20251226-024026-fastvit_ma36-256/model_best.pth.tar"
MODEL_NAME="fastvit_ma36"  # <-- Sửa lại nếu tên model khác

if [ -z "$CHECKPOINT" ]; then
	echo "Usage: $0 <checkpoint_path>"
	exit 1
fi

python3 tsm/train/fastvit/validation.py \
	"$DATA_DIR" \
	--model "$MODEL_NAME" \
	--checkpoint "$CHECKPOINT" \
	--batch-size 32 \
	--input-size 3 256 256 \
	--num-classes 3 \
	--workers 4 \
	--log-freq 10
