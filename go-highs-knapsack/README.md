# Nextmv Go HiGHS Knapsack

Example for running a Go application on the Nextmv Platform using the HiGHS
solver. We solve a knapsack Mixed Integer Programming problem.

1. Run the app.

    ```bash
    go run . -runner.input.path input.json \
      -runner.output.path output.json -solve.duration 10s
    ```

To push your app to the Nextmv platform via `nextmv app push ...`, you will
need to have [zig][zig] installed and available on your `$PATH`.

## Next steps

* Open `main.go` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[zig]: https://ziglang.org/download/
[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
