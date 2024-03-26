# Nextmv order fulfillment template

This is a Integer Programming model to solve the order fulfillment problem.

The order fulfillment problem is a typical decision problem in e-commerce and
the retailer industry. It needs to be determined which distribution centers
are used and which carriers should be considered for the transportation of
the order to the customer. Of course these are not all aspects of the order
fulfillment problem, but these decisions will be the focus of this model.

The most important files created are `main.go` and `input.json`.

* `main.go` implements a MIP knapsack solver.
* `input.json` is a sample input file that follows the input definition in
`main.go`.

Run the command below to see if everything works as expected:

```bash
go run . -runner.input.path input.json \
  -runner.output.path output.json -solve.duration 10s
```

A file `output.json` should have been created with a solution to the order
fulfillment problem.

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
* Further documentation, guides, and API references about custom modelling and
deployment can also be found on our [blog](https://www.nextmv.io/blog) and on
our [documentation site](https://docs.nextmv.io).
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!
