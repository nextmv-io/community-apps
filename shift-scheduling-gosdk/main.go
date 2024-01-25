// package main holds the implementation of the shift scheduling template.
package main

import (
	"context"
	"fmt"
	"log"
	"math"
	"time"

	"github.com/nextmv-io/sdk/mip"
	"github.com/nextmv-io/sdk/model"
	"github.com/nextmv-io/sdk/run"
	"github.com/nextmv-io/sdk/run/schema"
)

func main() {
	runner := run.CLI(solver)
	err := runner.Run(context.Background())
	if err != nil {
		log.Fatal(err)
	}
}

func solver(_ context.Context, input input, options options) (out schema.Output, retErr error) {
	// We solve a shift coverage problem using Mixed Integer Programming.
	// We solve this by generating all possible shifts
	// and then selecting a subset of these
	potentialAssignments, potentialAssignmentsPerWorker := potentialAssignments(input, options)
	demands := demands(input, potentialAssignments)
	m, x := newMIPModel(input, potentialAssignments, potentialAssignmentsPerWorker, demands, options)

	solver, err := mip.NewSolver(mip.Highs, m)
	if err != nil {
		return schema.Output{}, err
	}

	solution, err := solver.Solve(options.Solve)
	if err != nil {
		return schema.Output{}, err
	}

	// Format the solution into the desired output format and add custom
	// statistics.
	output := mip.Format(options, format(solution, x, potentialAssignments), solution)
	output.Statistics.Result.Custom = mip.DefaultCustomResultStatistics(m, solution)

	return output, nil
}

func format(
	solverSolution mip.Solution,
	x model.MultiMap[mip.Bool, assignment],
	assignments []assignment,
) output {
	if !solverSolution.IsOptimal() && !solverSolution.IsSubOptimal() {
		return output{}
	}
	nextShiftSolution := output{}
	usedWorkers := make(map[string]struct{})

	for _, assignment := range assignments {
		if solverSolution.Value(x.Get(assignment)) >= 0.9 {
			nextShiftSolution.AssignedShifts = append(nextShiftSolution.AssignedShifts, outputAssignment{
				Start:    assignment.Start,
				End:      assignment.End,
				WorkerID: assignment.Worker.ID,
			})
			if _, ok := usedWorkers[assignment.Worker.ID]; !ok {
				usedWorkers[assignment.Worker.ID] = struct{}{}
			}
		}
	}
	nextShiftSolution.NumberAssignedWorkers = len(usedWorkers)

	return nextShiftSolution
}

func newMIPModel(
	input input,
	potentialAssignments []assignment,
	potentialAssignmentsPerWorker map[string][]assignment,
	demandCovering map[string][]assignment,
	opts options,
) (mip.Model, model.MultiMap[mip.Bool, assignment]) {
	m := mip.NewModel()
	m.Objective().SetMinimize()

	x := model.NewMultiMap(
		func(...assignment) mip.Bool {
			return m.NewBool()
		}, potentialAssignments)

	underSupplySlack := model.NewMultiMap(
		func(demand ...requiredWorker) mip.Float {
			return m.NewFloat(0, float64(demand[0].Count))
		}, input.RequiredWorkers)

	overSupplySlack := model.NewMultiMap(
		func(demand ...requiredWorker) mip.Float {
			return m.NewFloat(0, math.MaxFloat64)
		}, input.RequiredWorkers)

	for _, demand := range input.RequiredWorkers {
		demandCover := demandCovering[demand.requiredWorkerID]
		// We need to cover all demands
		coverConstraint := m.NewConstraint(mip.Equal, float64(demand.Count))
		coverConstraint.NewTerm(1.0, underSupplySlack.Get(demand))
		coverConstraint.NewTerm(-1.0, overSupplySlack.Get(demand))
		coverPerWorker := map[string]mip.Constraint{}
		for _, assignment := range demandCover {
			constraint, ok := coverPerWorker[assignment.Worker.ID]
			if !ok {
				constraint = m.NewConstraint(mip.LessThanOrEqual, 1.0)
				coverPerWorker[assignment.Worker.ID] = constraint
			}
			constraint.NewTerm(1.0, x.Get(assignment))
			coverConstraint.NewTerm(1.0, x.Get(assignment))
		}
		m.Objective().NewTerm(opts.Penalty.OverSupply, overSupplySlack.Get(demand))
		m.Objective().NewTerm(opts.Penalty.UnderSupply, underSupplySlack.Get(demand))
	}

	// Two shift of a worker have to be at least x hours apart
	for _, worker := range input.Workers {
		for i, a1 := range potentialAssignmentsPerWorker[worker.ID] {
			// A worker can only work y hours per day
			lessThanXhoursPerDay := m.NewConstraint(mip.LessThanOrEqual, opts.Limits.Day.MaxDuration.Hours())
			lessThanXhoursPerDay.NewTerm(a1.Duration.Hours(), x.Get(a1))
			atLeastYhoursApart := m.NewConstraint(mip.LessThanOrEqual, 1.0)
			atLeastYhoursApart.NewTerm(1.0, x.Get(a1))
			lessThanZhoursPerWeek := m.NewConstraint(mip.LessThanOrEqual, opts.Limits.Week.MaxDuration.Hours())
			lessThanZhoursPerWeek.NewTerm(a1.Duration.Hours(), x.Get(a1))
			for _, a2 := range potentialAssignmentsPerWorker[worker.ID][i+1:] {
				durationApart := a1.DurationApart(a2)
				if durationApart > 0 {
					// if a1 and a2 do not at least have x hours between them, we
					// forbid them to be assigned at the same time
					if durationApart < opts.Limits.Shift.RecoveryTime {
						atLeastYhoursApart.NewTerm(1.0, x.Get(a2))
					}

					if durationApart < 24*time.Hour {
						lessThanXhoursPerDay.NewTerm(a2.Duration.Hours(), x.Get(a2))
					}

					if durationApart < 7*24*time.Hour {
						lessThanZhoursPerWeek.NewTerm(a2.Duration.Hours(), x.Get(a2))
					}
				}
			}
		}
	}

	return m, x
}

func potentialAssignments(input input, opts options) ([]assignment, map[string][]assignment) {
	potentialAssignments := make([]assignment, 0)
	potentialAssignmentsPerWorker := map[string][]assignment{}
	for _, worker := range input.Workers {
		potentialAssignmentsPerWorker[worker.ID] = make([]assignment, 0)
		for _, availability := range worker.Availability {
			for start := availability.Start; start.Before(availability.End); start = start.Add(30 * time.Minute) {
				for end := availability.End; start.Before(end); end = end.Add(-30 * time.Minute) {
					// make sure that end-start is not more than x hours
					duration := end.Sub(start)
					if duration > opts.Limits.Shift.MaxDuration {
						continue
					}
					// make sure that end-start is not less than y hours - we are
					// only shrinking the end time, so we can break here
					if duration < opts.Limits.Shift.MinDuration {
						break
					}
					assignment := assignment{
						AssignmentID: fmt.Sprint(len(potentialAssignments)),
						Start:        start,
						End:          end,
						Worker:       worker,
						Duration:     duration,
					}
					potentialAssignmentsPerWorker[worker.ID] = append(potentialAssignmentsPerWorker[worker.ID], assignment)
					potentialAssignments = append(potentialAssignments, assignment)
				}
			}
		}
	}
	return potentialAssignments, potentialAssignmentsPerWorker
}

func demands(input input, potentialAssignments []assignment) map[string][]assignment {
	// initialize demand ids
	for i, demand := range input.RequiredWorkers {
		demand.requiredWorkerID = fmt.Sprint(i)
		input.RequiredWorkers[i] = demand
	}

	demandCovering := map[string][]assignment{}
	for _, demand := range input.RequiredWorkers {
		demandCovering[demand.requiredWorkerID] = []assignment{}
		for i, potentialAssignment := range potentialAssignments {
			if (potentialAssignment.Start.Before(demand.Start) || potentialAssignment.Start.Equal(demand.Start)) &&
				(potentialAssignment.End.After(demand.End) || potentialAssignment.End.Equal(demand.End)) {
				potentialAssignments[i].DemandsCovered = append(potentialAssignments[i].DemandsCovered, demand)
				demandCovering[demand.requiredWorkerID] = append(demandCovering[demand.requiredWorkerID], potentialAssignment)
			}
		}
	}
	return demandCovering
}
