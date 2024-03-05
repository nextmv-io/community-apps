// package main holds the implementation of the mip-knapsack template.
package main

import (
	"context"
	"log"

	"github.com/nextmv-io/go-highs"
	"github.com/nextmv-io/go-mip"
	"github.com/nextmv-io/sdk/run"
	"github.com/nextmv-io/sdk/run/schema"
)

// This template demonstrates how to solve a Mixed Integer Programming problem.
// To solve a mixed integer problem is to optimize a linear objective function
// of many variables, subject to linear constraints. We demonstrate this by
// solving the well known knapsack problem.
func main() {
	err := run.CLI(solver).Run(context.Background())
	if err != nil {
		log.Fatal(err)
	}
}

// The options for the solver.
type options struct {
	Solve mip.SolveOptions `json:"solve,omitempty"`
}

// Input of the problem.
type input struct {
	Items          []item  `json:"items"`
	WeightCapacity float64 `json:"weight_capacity"`
}

// An item has a Value and Weight. ID is used to identify the item.
type item struct {
	ID     string  `json:"id,omitempty"`
	Value  float64 `json:"value"`
	Weight float64 `json:"weight"`
}

// solution represents the decisions made by the solver.
type solution struct {
	Items []item `json:"items,omitempty"`
}

// solver is the entrypoint of the program where a model is defined and solved.
func solver(_ context.Context, input input, options options) (schema.Output, error) {
	// Translate the input to a MIP model.
	model, variables := model(input)

	// Create a solver using a provider. Please see the documentation on
	// [mip.SolverProvider] for more information on the available providers.
	solver := highs.NewSolver(model)

	// Solve the model and get the solution.
	solution, err := solver.Solve(options.Solve)
	if err != nil {
		return schema.Output{}, err
	}

	// Format the solution into the desired output format and add custom
	// statistics.
	output := mip.Format(options, format(input, solution, variables), solution)
	output.Statistics.Result.Custom = mip.DefaultCustomResultStatistics(model, solution)

	return output, nil
}

// model creates a MIP model from the input. It also returns the decision
// variables.
func model(input input) (mip.Model, map[string]mip.Bool) {
	// We start by creating a MIP model.
	model := mip.NewModel()

	// Create a map of ID to decision variables for each item in the knapsack.
	itemVariables := make(map[string]mip.Bool, len(input.Items))
	for _, item := range input.Items {
		// Create a new binary decision variable for each item in the knapsack.
		itemVariables[item.ID] = model.NewBool()
	}

	// We want to maximize the value of the knapsack.
	model.Objective().SetMaximize()

	// This constraint ensures the weight capacity of the knapsack will not be
	// exceeded.
	capacityConstraint := model.NewConstraint(
		mip.LessThanOrEqual,
		input.WeightCapacity,
	)

	// For each item, set the term in the objective function and in the
	// constraint.
	for _, item := range input.Items {
		// Sets the value of the item in the objective function.
		model.Objective().NewTerm(item.Value, itemVariables[item.ID])

		// Sets the weight of the item in the constraint.
		capacityConstraint.NewTerm(item.Weight, itemVariables[item.ID])
	}

	return model, itemVariables
}

// format the solution from the solver into the desired output format.
func format(input input, solverSolution mip.Solution, itemVariables map[string]mip.Bool) solution {
	if !solverSolution.IsOptimal() && !solverSolution.IsSubOptimal() {
		return solution{}
	}

	items := make([]item, 0)
	for _, item := range input.Items {
		if solverSolution.Value(itemVariables[item.ID]) > 0.9 {
			items = append(items, item)
		}
	}

	return solution{
		Items: items,
	}
}
