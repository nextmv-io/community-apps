# Nextmv shift scheduling template

`shift-scheduling` is a MIP-based shift-scheduling model. This template will get
you up to speed deploying your own solution.

The most important files created are `main.go` and `input.json`.

`main.go` implements shift-scheduling model to be solved. `input.json` is a
sample input file that follows the input definition in `main.go`. The input
holds firstly a set of workers with an `id` and availability times. Secondly, it
contains a set of `required workers`, each describing a time window and the
number of workers that are required to work during this time.

You should be able to run the following command:

```bash
go run . -runner.input.path input.json \
  -runner.output.path output.json -solve.duration 10s
```

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

* For more information about our platform, please visit: <https://docs.nextmv.io>.
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!
