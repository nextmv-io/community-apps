package mip

import (
	"os"
	"path"
	"testing"

	"github.com/nextmv-io/sdk/golden"
)

func TestMain(m *testing.M) {
	code := m.Run()
	os.Exit(code)
}

func TestGolden(t *testing.T) {
	wd, _ := os.Getwd()
	golden.FileTests(
		t,
		"inputs",
		golden.Config{
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
				Command:    "python3",
				Args:       []string{"main.py"},
				InputFlag:  "-input",
				OutputFlag: "-output",
				WorkDir: path.Join(wd, "..", "..", "..", "python-xpress-park-location"),
			},
		},
	)
}
