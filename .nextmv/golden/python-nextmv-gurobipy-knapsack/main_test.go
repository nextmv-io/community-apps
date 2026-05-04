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
			Args: []string{
				"-TimeLimit",
				"30",
			},
			TransientFields: []golden.TransientField{
				{
					Key:         "$.metrics.total_duration",
					Replacement: golden.StableFloat,
				},
				{
					Key:         "$.metrics.solve_duration",
					Replacement: golden.StableFloat,
				},
			},
			ExecutionConfig: &golden.ExecutionConfig{
				Command:    "uv",
				Args:       []string{"run", "--directory", "../../../python-nextmv-gurobipy-knapsack", "main.py"},
			},
		},
	)
}
