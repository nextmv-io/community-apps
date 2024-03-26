# README tests

The README testing makes sure that all commands mentioned in the README.md files
of the apps are working as expected. Furthermore, the commands and their output
are persisted to be used in docs and detect changes in the output.

## Usage

Update the commands:

```bash
python readme-extract-commands.py --update
```

Update the expectations / re-run the tests:

```bash
go test ./... --update
```

Add any special handling for certain commands (e.g.: do not test their output /
silence them) to the `workflow-configuration.yml` file.
