FROM mcr.microsoft.com/dotnet/sdk:8.0

ARG ARCH=arm64

# Build the app.
WORKDIR /app
COPY . .
RUN dotnet publish --os linux --arch $ARCH --self-contained
