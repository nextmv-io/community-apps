cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/hexaly:latest \
sh -c 'pip install -r requirements.txt > /dev/null && python3 /app/main.py'
