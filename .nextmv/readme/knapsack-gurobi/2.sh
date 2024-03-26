cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/gurobi:latest \
python3 /app/main.py