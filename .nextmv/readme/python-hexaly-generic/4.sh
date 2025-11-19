docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/python:3.11 \
sh -c 'pip install -r /app/requirements.txt && python3 /app/main.py inFileName=inputs/input.dat solFileName=output.txt'
