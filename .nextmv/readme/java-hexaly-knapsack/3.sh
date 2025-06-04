mvn package && cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/java:latest \
java -jar /app/main.jar
