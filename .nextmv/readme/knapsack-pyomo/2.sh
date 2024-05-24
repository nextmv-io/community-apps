cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/pyomo:latest \
sh -c 'python3 /app/main.py'
