package main

import (
	"time"

	"github.com/nextmv-io/sdk/mip"
)

// output holds the output data of the solution.
type output struct {
	AssignedShifts        []outputAssignment `json:"assigned_shifts"`
	NumberAssignedWorkers int                `json:"number_assigned_workers"`
}

// options holds custom configuration data.
type options struct {
	Penalty penalty          `json:"penalty" usage:"set penalties for over and under supply of workers"`
	Limits  limits           `json:"limits" usage:"holds fields to configure the models limits"`
	Solve   mip.SolveOptions `json:"solve" usage:"holds fields to configure the solver"`
}

type limits struct {
	Shift struct {
		MinDuration  time.Duration `json:"min_duration" default:"2h" usage:"minimum working time per shift"`
		MaxDuration  time.Duration `json:"max_duration" default:"8h" usage:"maximum working time per shift"`
		RecoveryTime time.Duration `json:"recovery_time" default:"8h" usage:"minimum time between shifts"`
	} `json:"shift"`
	Week struct {
		MaxDuration time.Duration `json:"max_duration" default:"40h" usage:"maximum working time per week"`
	} `json:"week"`
	Day struct {
		MaxDuration time.Duration `json:"max_duration" default:"10h" usage:"maximum working time per day"`
	} `json:"day"`
}

type penalty struct {
	OverSupply  float64 `json:"over_supply" default:"1000" usage:"penalty for over-supplying a demand"`
	UnderSupply float64 `json:"under_supply" default:"500" usage:"penalty for under-supplying a demand"`
}

// input represents a struct definition that can read input.json.
type input struct {
	Workers         []worker         `json:"workers"`
	RequiredWorkers []requiredWorker `json:"required_workers"`
}

// worker holds worker specific data.
type worker struct {
	Availability []availability `json:"availability"`
	ID           string         `json:"id"`
}

// availability holds available times for a worker.
type availability struct {
	Start time.Time `json:"start"`
	End   time.Time `json:"end"`
}

// requiredWorker holds data about times and number of required workers per time window.
type requiredWorker struct {
	requiredWorkerID string    `json:"-"`
	Start            time.Time `json:"start"`
	End              time.Time `json:"end"`
	Count            int       `json:"count"`
}

// ID returned the RequiredWorker ID.
func (r requiredWorker) ID() string {
	return r.requiredWorkerID
}

// outputAssignment holds an assignment for a worker.
type outputAssignment struct {
	Start    time.Time `json:"start"`
	End      time.Time `json:"end"`
	WorkerID string    `json:"worker_id"`
}

// assignment represents a shift assignment.
type assignment struct {
	DemandsCovered []requiredWorker `json:"demands_covered"`
	Start          time.Time        `json:"start"`
	End            time.Time        `json:"end"`
	Worker         worker           `json:"worker"`
	Duration       time.Duration    `json:"duration"`
	AssignmentID   string           `json:"assignment_id"`
}

// DurationApart calculates the time to assignments are apart from each other.
func (a assignment) DurationApart(other assignment) time.Duration {
	if a.Start.After(other.End) {
		return a.Start.Sub(other.End)
	}
	if a.End.Before(other.Start) {
		return other.Start.Sub(a.End)
	}
	return 0
}

// ID returns the assignment id.
func (a assignment) ID() string {
	return a.AssignmentID
}
