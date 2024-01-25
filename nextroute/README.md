# Nextmv nextroute template

`nextroute` is a modeling kit for vehicle routing problems (VRP). This template
will get you up to speed deploying your own solution.

The most important files created are `main.go` and `input.json`.

`main.go` implements a VRP solver with many real world features already
configured. `input.json` is a sample input file that follows the input
definition in `main.go`.

Run the command below to check that everything works as expected:

```bash
nextmv sdk run . -- -runner.input.path input.json \
  -runner.output.path output.json -solve.duration 10s
```

A file `output.json` should have been created with a VRP solution.

## Next steps

* For more information about our platform, please visit: <https://docs.nextmv.io>.
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!
