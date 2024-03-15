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
					Key:         ".statistics.result.duration",
					Replacement: golden.StableFloat,
				},
				{
					Key:         ".statistics.run.duration",
					Replacement: golden.StableFloat,
				},
			},
			ExecutionConfig: &golden.ExecutionConfig{
				Command:    "python3",
				Args:       []string{"../../../knapsack-ampl/main.py"},
				InputFlag:  "-input",
				OutputFlag: "-output",
			},
		},
	)
}
