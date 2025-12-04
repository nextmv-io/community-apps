# Rust knapsack with good_lp

This app solves the knapsack problem using the [good_lp](https://crates.io/crates/good_lp) crate.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Rust](https://www.rust-lang.org/tools/install)
- Some dependencies for building HiGHS as the underlying solver. On Ubuntu, you can install them with:

    ```bash
    sudo apt install -y build-essential cmake libclang-dev
    ```

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
