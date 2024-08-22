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
			UseStdIn:  true,
			UseStdOut: true,
			ExecutionConfig: &golden.ExecutionConfig{
				Command: "python3",
				Args:    []string{"../../../hello-world/main.py"},
			},
		},
	)
}
