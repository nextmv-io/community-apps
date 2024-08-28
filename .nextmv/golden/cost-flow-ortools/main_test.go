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
			Args: []string{},
			TransientFields: []golden.TransientField{
				{
					Key:         "$.statistics.result.duration",
					Replacement: float64(0.015),
				},
				{
					Key:         "$.statistics.run.duration",
					Replacement: float64(0.015),
				},
			},
			DedicatedComparison: []string{
				"$.statistics.result.value",
			},
			ExecutionConfig: &golden.ExecutionConfig{
				Command:    "python3",
				Args:       []string{"../../../cost-flow-ortools/main.py"},
				InputFlag:  "-input",
				OutputFlag: "-output",
			},
		},
	)
}
