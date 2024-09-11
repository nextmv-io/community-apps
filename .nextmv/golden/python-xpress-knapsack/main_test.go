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
			Args: []string{
				"-duration",
				"30",
			},
			TransientFields: []golden.TransientField{
				{
					Key:         "$.statistics.result.duration",
					Replacement: golden.StableFloat,
				},
				{
					Key:         "$.statistics.run.duration",
					Replacement: golden.StableFloat,
				},
				{
					Key:         "$.options.output",
					Replacement: "output.json",
				},
				{
					Key:         "$.options.input",
					Replacement: "input.json",
				},
			},
			// We ignore stdout here, as it may contain community license
			// warnings depending on whether a license was set up or not (not
			// the intention of the test).
			IgnoreStdOut: true,
			ExecutionConfig: &golden.ExecutionConfig{
				Command:    "python3",
				Args:       []string{"../../../python-xpress-knapsack/main.py"},
				InputFlag:  "-input",
				OutputFlag: "-output",
			},
		},
	)
}
