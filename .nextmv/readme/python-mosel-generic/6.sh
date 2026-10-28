docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/python:3.11 \
sh -c 'cd /app && pip install -r requirements.txt && python3 main.py'
