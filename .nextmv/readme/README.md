# README tests

The README testing makes sure that all commands mentioned in the README.md files
of the apps are working as expected. Furthermore, the commands and their output
are persisted to be used in docs and detect changes in the output.

## Usage

Update the commands:

```bash
python readme-extract-commands.py --update
```

Change the configuration for the app (if needed) or add a new one. This is done
in the `workflow-configuration.yml` file.

Update the expectations / re-run the tests:

```bash
go test -v ./... --update
```

Add any special handling for certain commands (e.g.: do not test their output /
silence them) to the `workflow-configuration.yml` file.

Run only a specific test and update its expectations (here: `go-hello-world` app
and its first README command):

```bash
go test -v -run TestGolden/go-hello-world/0.sh -update ./...
```

If you only want to run specific tests, you can filter them via the `--filter`
flag which accepts a regex and allows filtering based on test name. E.g.: to run
only the tests for the `region-allocation` app (and update the expectations):

```bash
go test ./... --filter '.*region-allocation.*' --update
```

Or for only running their first command:

```bash
go test ./... --filter '.*region-allocation.*/0.sh' --update
```
