// Package main holds the implementation for the app.
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/nextmv-io/sdk/run"
	"github.com/nextmv-io/sdk/run/statistics"
)

func main() {
	// Read the input from stdin.
	err := run.CLI(solver).Run(context.Background())
	if err != nil {
		log.Fatal(err)
	}
}

type input struct {
	Name string `json:"name"`
}

type output struct {
	Options    options                `json:"options"`
	Solution   any                    `json:"solution"`
	Statistics *statistics.Statistics `json:"statistics"`
}

type options struct{}

func solver(_ context.Context, input input, options options) (output, error) {
	name := input.Name

	// ##### Insert model here

	// Print logs that render in the run view in Nextmv Console.
	message := fmt.Sprintf("Hello, %s", name)
	fmt.Fprintln(os.Stderr, message)

	// Write output and statistics.
	stats := statistics.NewStatistics()
	stats.Result = &statistics.Result{}
	value := statistics.Float64(1.23)
	stats.Result.Value = &value
	stats.Result.Custom = map[string]any{"message": message}
	output := output{
		Options:    options,
		Solution:   map[string]any{},
		Statistics: stats,
	}

	return output, nil
}
