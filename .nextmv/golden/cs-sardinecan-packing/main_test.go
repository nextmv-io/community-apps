package mip

import (
	"os"
	"testing"

	"github.com/nextmv-io/sdk/golden"
)

func TestMain(m *testing.M) {
	code := m.Run()
	golden.Reset([]string{"inputs", "main_test.go"})
	os.Exit(code)
}

func TestGolden(t *testing.T) {
	golden.FileTests(
		t,
		"inputs",
		golden.Config{
			Args:      []string{},
			UseStdIn:  true,
			UseStdOut: true,
			ExecutionConfig: &golden.ExecutionConfig{
				Command: "dotnet",
				Args:    []string{"run", "--project", "../../../cs-sardinecan-packing/cs-sardinecan-packing.csproj"},
			},
		},
	)
}
