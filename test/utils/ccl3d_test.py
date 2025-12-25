import numpy as np
import nibabel as nib
import ccl3d

def main():
	img = nib.load('resource/video/pancreas_001_data.nii')
	data = img.get_fdata()
	binary = (data > 0).astype(np.uint8)
	print(f"Input shape: {binary.shape}, unique values: {np.unique(binary)}")

	# Chạy connected component labeling
	labels = ccl3d.ccl3d(binary)
	print(f"Output shape: {labels.shape}, unique labels: {np.unique(labels)}")

if __name__ == "__main__":
	main()
