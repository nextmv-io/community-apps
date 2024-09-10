# Nextmv Go HiGHS Order Fulfillment

Example for running a Go application on the Nextmv Platform using the HiGHS
solver. We solve an order fulfillment problem. We need to decide which
distribution centers are used and which carriers should be considered for the
transportation of the order to the customer.

1. Run the app.

    ```bash
    go run . -runner.input.path input.json \
      -runner.output.path output.json -solve.duration 10s
    ```

To push your app to the Nextmv platform via `nextmv app push ...`, you will
need to have [zig][zig] installed and available on your `$PATH`.

## Mirror running on Nextmv Cloud locally

Docker needs to be installed.

To run the application in the same Docker image as the one used on Nextmv
Cloud, you can use the following command:

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

* Open `main.go` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[zig]: https://ziglang.org/download/
[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
