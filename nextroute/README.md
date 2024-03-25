# Nextmv nextroute template

`nextroute` is a modeling kit for vehicle routing problems (VRP). This template
will get you up to speed deploying your own solution.

The most important files created are `main.go` and `input.json`.

`main.go` implements a VRP solver with many real world features already
configured. `input.json` is a sample input file that follows the input
definition in `main.go`.

Run the command below to check that everything works as expected:

```bash
go run . -runner.input.path input.json \
  -runner.output.path output.json -solve.duration 10s
```

A file `output.json` should have been created with a VRP solution.

## Mirror running on Nextmv Cloud locally

Pre-requisites: Docker needs to be installed.

To run the application locally in the same docker image as the one used on the
Nextmv Cloud, you can use the following command:

```bash
GOOS=linux go build . && \
docker run -i --rm -v $(pwd):/app ghcr.io/nextmv-io/runtime/default:latest \
/app/nextroute --runner.input.path input.json --runner.output.path output.json
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by using
the command `Dev Containers: Reopen in Container`.

## Next steps

* For more information about our platform, please visit: <https://docs.nextmv.io>.
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!
