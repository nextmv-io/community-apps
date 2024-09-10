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
			Args:            []string{},
			TransientFields: []golden.TransientField{},
			Thresholds: golden.Tresholds{
				Float: 0.01,
			},
			ExecutionConfig: &golden.ExecutionConfig{
				Command:    "go",
				Args:       []string{"run", "."},
				InputFlag:  "-runner.input.path",
				OutputFlag: "-runner.output.path",
				WorkDir:    "../../../go-hello-world",
			},
		},
	)
}
