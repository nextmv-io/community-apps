# Rust echo app

A simple echo app written in Rust.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Rust](https://www.rust-lang.org/tools/install)

## Usage

To run the app, use the following command:

```bash
cat input.json | cargo run
```

To push and run the app on the Nextmv platform, use:

```bash
nextmv app push -a <app-id>
nextmv app run -a <app-id> -i input.json --wait
```
