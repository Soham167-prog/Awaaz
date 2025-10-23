import argparse
import os
import sys
import subprocess

DEFAULT_CKPT = "checkpoints/best.pt"


def main():
	parser = argparse.ArgumentParser(description="Simple predictor")
	parser.add_argument("image", help="Path to image")
	parser.add_argument("--ckpt", default=DEFAULT_CKPT)
	args = parser.parse_args()

	if not os.path.isfile(args.ckpt):
		print(f"Checkpoint not found: {args.ckpt}")
		sys.exit(1)
	if not os.path.isfile(args.image):
		print(f"Image not found: {args.image}")
		sys.exit(1)

	cmd = [sys.executable, "src/app/predict.py", "--checkpoint", args.ckpt, "--image", args.image]
	proc = subprocess.run(cmd)
	sys.exit(proc.returncode)


if __name__ == "__main__":
	main()
