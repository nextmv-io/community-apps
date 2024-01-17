# Nextmv shift scheduling template

`shift-scheduling` is a MIP-based shift-scheduling model. This template will get
you up to speed deploying your own solution.

The most important files created are `main.go` and `input.json`.

`main.go` implements shift-scheduling model to be solved. `input.json` is a
sample input file that follows the input definition in `main.go`. The input
holds firstly a set of workers with an `id` and availability times. Secondly, it
contains a set of `required workers`, each describing a time window and the
number of workers that are required to work during this time.

You should be able to run the following command. It assumes that you gave your
app the app-id `shift-scheduling`:

```bash
nextmv sdk run . -- -runner.input.path input.json \
  -runner.output.path output.json -solve.duration 10s
```

## Next steps

* For more information about our platform, please visit: <https://docs.nextmv.io>.
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!
