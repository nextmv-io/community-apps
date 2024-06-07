# Golden file tests

This directory contains golden file tests for the apps contained in this
repository. These tests use the [`golden` package](https://github.com/nextmv-io/sdk/tree/develop/golden)
of the Nextmv SDK to compare the output of the apps to a set of golden files.
Each app has its own subdirectory containing the golden files for that app.

## Update expectations

To update the golden files, simply run this command from this directory (or from
the directory of the app you want to update):

```bash
go test ./... --update
```
