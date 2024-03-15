package mip

import (
	"os"
	"os/exec"
	"testing"

	"github.com/nextmv-io/sdk/golden"
)

func TestMain(m *testing.M) {
	prepareApp()
	code := m.Run()
	golden.Reset([]string{"inputs", "main_test.go"})
	os.Exit(code)
}

// prepareApp builds the app and moves the resulting jar to this directory
func prepareApp() {
	build := exec.Command("mvn", "package")
	build.Dir = "../../../knapsack-java-ortools"
	err := build.Run()
	if err != nil {
		panic(err)
	}

	err = os.Rename("../../../knapsack-java-ortools/main.jar", "main.jar")
	if err != nil {
		panic(err)
	}
}

func TestGolden(t *testing.T) {
	golden.FileTests(
		t,
		"inputs",
		golden.Config{
			Args: []string{
				"--duration",
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
				Command:    "java",
				Args:       []string{"-jar", "main.jar"},
				InputFlag:  "--input",
				OutputFlag: "--output",
			},
		},
	)
}
