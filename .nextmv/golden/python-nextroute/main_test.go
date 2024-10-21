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
				"-solve_duration", "3",
				// for deterministic tests
				"-format_disable_progression", "true",
				"-solve_parallelruns", "1",
				"-solve_iterations", "50",
				"-solve_rundeterministically", "true",
				"-solve_startsolutions", "1",
			},
			TransientFields: []golden.TransientField{
				{Key: "$.statistics.result.duration", Replacement: golden.StableFloat},
				{Key: "$.statistics.run.duration", Replacement: golden.StableFloat},
				{Key: "$.options.output", Replacement: "output.json"},
				{Key: "$.options.input", Replacement: "input.json"},
			},
			Thresholds: golden.Tresholds{
				Float: 0.01,
			},
			ExecutionConfig: &golden.ExecutionConfig{
				Command:    "python3",
				Args:       []string{"../../../python-nextroute/main.py"},
				InputFlag:  "-input",
				OutputFlag: "-output",
			},
		},
	)
}
