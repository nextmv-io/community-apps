package mip

import (
	"os"
	"testing"

	"github.com/nextmv-io/sdk/golden"
)

func TestMain(m *testing.M) {
	code := m.Run()
	os.Exit(code)
}

func TestGolden(t *testing.T) {
	golden.FileTests(
		t,
		"inputs",
		golden.Config{
			UseStdIn: true,
			UseStdOut: true,
			Args: []string{},
			DedicatedComparison:[]string{
				"$.metrics.status",
				"$.metrics.variables",
				"$.metrics.constraints",
			},
			// We ignore stdout here, as it may contain community license
			// warnings depending on whether a license was set up or not (not
			// the intention of the test).
			IgnoreStdOut: true,
			ExecutionConfig: &golden.ExecutionConfig{
				Command:    "uv",
				Args:       []string{"run", "--directory", "../../../python-xpress-park-location", "main.py"},
			},
		},
	)
}
