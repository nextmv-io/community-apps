// Package main holds the implementation for the app.
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/nextmv-io/sdk/run"
)

func main() {
	err := run.CLI(solver).Run(context.Background())
	if err != nil {
		log.Fatal(err)
	}
}

type input struct {
	Name string `json:"name"`
}

type output struct {
	Options    options        `json:"options"`
	Solution   any            `json:"solution"`
	Statistics map[string]any `json:"statistics"`
}

type options struct{}

func solver(_ context.Context, input input, options options) (output, error) {
	name := input.Name

	// ##### Insert model here

	// Print logs that render in the run view in Nextmv Console
	fmt.Fprintf(os.Stderr, "Hello, %s\n", name)

	// Write output and statistics.
	output := output{
		Options:  options,
		Solution: map[string]any{},
		Statistics: map[string]any{
			"message": "Hello, " + name,
		},
	}

	return output, nil
}
