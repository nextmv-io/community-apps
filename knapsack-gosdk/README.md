# Nextmv MIP template

This template demonstrates how to solve a Mixed Integer Programming problem
using the open-source solver [HiGHS](https://github.com/ERGO-Code/HiGHS) with
the Nextmv Go SDK.

To solve a Mixed Integer Problem (MIP) is to optimize a linear objective
function of many variables, subject to linear constraints. We demonstrate this
by solving the knapsack problem.

Knapsack is a classic combinatorial optimization problem. Given a collection of
items with a value and weight, our objective is to maximize the total value
without exceeding the weight capacity of the knapsack.

The input defines a number of items which have an id to identify the item, a
weight and a value. Additionally there is a weight capacity.

The most important files created are `main.go` and `input.json`.

* `main.go` implements a MIP knapsack solver.
* `input.json` is a sample input file that follows the input definition in
`main.go`.

Run the command below to check that everything works as expected:

```bash
go run . -runner.input.path input.json \
  -runner.output.path output.json -solve.duration 10s
```

A file `output.json` should have been created with the optimal knapsack
solution.

## Push pre-requisites

To push your app to the Nextmv platform via `nextmv app push ...`, you will need
to have [_zig_](https://ziglang.org/download/) installed and available on your
`$PATH`.

## Mirror running on Nextmv Cloud locally

Pre-requisites: Docker needs to be installed.

To run the application locally in the same docker image as the one used on the
Nextmv Cloud, you can use the following command:

```bash
GOOS=linux go build -o main . && \
cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/default:latest \
/app/main
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by using
the command `Dev Containers: Reopen in Container`.

## Next steps

* Open `main.go` and read through the comments to understand the model.
* API documentation and examples can be found in the [package
  documentation](https://pkg.go.dev/github.com/nextmv-io/sdk/mip).
* Further documentation, guides, and API references about custom modeling and
  deployment can also be found on our [blog](https://www.nextmv.io/blog) and on
  our [documentation site](https://docs.nextmv.io).
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!
