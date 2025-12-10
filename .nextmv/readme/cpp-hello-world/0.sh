# Configure aarch64 or amd64 build in app.yaml
nextmv app push -a <app-id>
echo '{"hello":"memory"}' | nextmv app run -a <app-id> --tail
