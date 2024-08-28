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
				"-solve.duration", "3s",
				// for deterministic tests
				"-format.disable.progression",
				"-solve.parallelruns", "1",
				"-solve.iterations", "50",
				"-solve.rundeterministically",
				"-solve.startsolutions", "1",
			},
			TransientFields: []golden.TransientField{
				{Key: "$.version.sdk", Replacement: golden.StableVersion},
				{Key: "$.version.nextroute", Replacement: golden.StableVersion},
				{Key: "$.statistics.result.duration", Replacement: golden.StableFloat},
				{Key: "$.statistics.run.duration", Replacement: golden.StableFloat},
			},
			Thresholds: golden.Tresholds{
				Float: 0.01,
			},
			ExecutionConfig: &golden.ExecutionConfig{
				Command:    "go",
				Args:       []string{"run", "."},
				InputFlag:  "-runner.input.path",
				OutputFlag: "-runner.output.path",
				WorkDir:    "../../../nextroute",
			},
		},
	)
}
