cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/xpress:latest \
python3 /app/main.py
