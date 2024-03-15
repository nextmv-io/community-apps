// package main holds the implementation of a order fulfillment problem.
package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"math"

	"github.com/nextmv-io/sdk"
	"github.com/nextmv-io/sdk/mip"
	"github.com/nextmv-io/sdk/model"
	"github.com/nextmv-io/sdk/run"
	"github.com/nextmv-io/sdk/run/schema"
	"github.com/nextmv-io/sdk/run/statistics"
)

func main() {
	err := run.CLI(solver).Run(context.Background())
	if err != nil {
		log.Fatal(err)
	}
}

type input struct {
	Items                           []item                                     `json:"items"`
	DistributionCenters             []distributionCenter                       `json:"distribution_centers"`
	CarrierCapacities               map[string]map[string]float64              `json:"carrier_capacities"`
	CarrierDeliveryCosts            map[string]map[string]map[string][]float64 `json:"carrier_delivery_costs"`
	CartonVolume                    float64                                    `json:"carton_volume"`
	CarrierDimensionalWeightFactors map[string]float64                         `json:"carrier_dimensional_weight_factors"`
}

// An item has a unique ID, an ordered quantity and a volume.
type item struct {
	ItemID     string  `json:"item_id"`
	Quantity   float64 `json:"quantity"`
	UnitVolume float64 `json:"unit_volume"`
	UnitWeight float64 `json:"unit_weight"`
}

// ID is implemented to fulfill the model.Identifier interface.
func (i item) ID() string {
	return i.ItemID
}

type distributionCenter struct {
	DistributionCenterID string         `json:"distribution_center_id"`
	Inventory            map[string]int `json:"inventory"`
	HandlingCost         float64        `json:"handling_cost"`
}

func (i distributionCenter) ID() string {
	return i.DistributionCenterID
}

type carrier struct {
	DistributionCenter distributionCenter `json:"distribution_center"`
	Carrier            string             `json:"carrier"`
}

func (i carrier) ID() string {
	return i.DistributionCenter.DistributionCenterID + "-" + i.Carrier
}

type assignment struct {
	Item               item               `json:"item"`
	DistributionCenter distributionCenter `json:"distribution_center"`
	Carrier            string             `json:"carrier"`
	Quantity           int                `json:"quantity"`
}

func (i assignment) ID() string {
	return i.Item.ItemID + "-" + i.DistributionCenter.DistributionCenterID + "-" + i.Carrier + "-" + fmt.Sprint(i.Quantity)
}

type assignmentOutput struct {
	ItemID               string `json:"item_id"`
	Quantity             int    `json:"quantity"`
	DistributionCenterID string `json:"distribution_center_id"`
	CarrierID            string `json:"carrier_id"`
}

// The options for the solver.
type options struct {
	Solve mip.SolveOptions `json:"solve,omitempty"`
}

func computeAssignments(i input) []assignment {
	assignments := []assignment{}
	for _, it := range i.Items {
		for _, dc := range i.DistributionCenters {
			for c := range i.CarrierCapacities[dc.DistributionCenterID] {
				for q := 0; q < int(it.Quantity); q++ {
					newAssignment := assignment{
						Item:               it,
						DistributionCenter: dc,
						Carrier:            c,
						Quantity:           q + 1,
					}
					assignments = append(assignments, newAssignment)
				}
			}
		}
	}
	return assignments
}

func solver(_ context.Context, i input, opts options) (schema.Output, error) {
	// We start by creating a MIP model.
	m := mip.NewModel()

	// used in constraints as a bound
	totalWeight := 0.0
	for _, order := range i.Items {
		totalWeight += order.Quantity * order.UnitWeight
	}

	// create assignments (item, dc, carrier combinations)
	assignments := computeAssignments(i)

	// create some helping data structures
	distributionCenterCarrierCombinations := []carrier{}
	for _, dc := range i.DistributionCenters {
		for c := range i.CarrierCapacities[dc.DistributionCenterID] {
			newCarrier := carrier{
				DistributionCenter: dc,
				Carrier:            c,
			}
			distributionCenterCarrierCombinations = append(distributionCenterCarrierCombinations, newCarrier)
		}
	}

	itemToAssignments := make(map[string][]assignment, len(i.Items))
	distributionCenterToCarrierToAssignments := make(map[string]map[string][]assignment, len(i.DistributionCenters))
	for _, as := range assignments {
		itemID := as.Item.ItemID
		_, ok := itemToAssignments[itemID]
		if !ok {
			itemToAssignments[itemID] = []assignment{}
		}
		itemToAssignments[itemID] = append(itemToAssignments[itemID], as)
		if _, ok = distributionCenterToCarrierToAssignments[as.DistributionCenter.DistributionCenterID]; !ok {
			distributionCenterToCarrierToAssignments[as.DistributionCenter.DistributionCenterID] = make(map[string][]assignment)
		}
		if _, ok = distributionCenterToCarrierToAssignments[as.DistributionCenter.DistributionCenterID][as.Carrier]; !ok {
			distributionCenterToCarrierToAssignments[as.DistributionCenter.DistributionCenterID][as.Carrier] = []assignment{}
		}
		distributionCenterToCarrierToAssignments[as.DistributionCenter.DistributionCenterID][as.Carrier] =
			append(distributionCenterToCarrierToAssignments[as.DistributionCenter.DistributionCenterID][as.Carrier], as)
	}

	// x is a multimap representing a set of variables. It is initialized with a
	// create function and, in this case one set of elements. The elements can
	// be used as an index to the multimap. To retrieve a variable, call
	// x.Get(element) where element is an element from the index set.
	x := model.NewMultiMap(
		func(...assignment) mip.Bool {
			return m.NewBool()
		}, assignments)

	// create another multimap which will hold the info about the number of
	// cartons at each distribution center.
	cartons := model.NewMultiMap(
		func(...carrier) mip.Float {
			return m.NewFloat(0.0, 1000.0)
		}, distributionCenterCarrierCombinations)

	// multimap for the total volume for each distribution center carrier
	// combination.
	volumes := model.NewMultiMap(
		func(...carrier) mip.Float {
			return m.NewFloat(0.0, 1000.0)
		}, distributionCenterCarrierCombinations)

	// multimap for the total weight for each distribution center carrier
	// combination.
	weights := model.NewMultiMap(
		func(...carrier) mip.Float {
			return m.NewFloat(0.0, 1000.0)
		}, distributionCenterCarrierCombinations)

	// multimap for the dimensional weights for each distribution center carrier
	// combination.
	dimensionalWeights := model.NewMultiMap(
		func(...carrier) mip.Float {
			return m.NewFloat(0.0, 1000.0)
		}, distributionCenterCarrierCombinations)

	// multimap for the billable weights for each distribution center carrier
	// combination.
	billableWeights := model.NewMultiMap(
		func(...carrier) mip.Float {
			return m.NewFloat(0.0, 1000.0)
		}, distributionCenterCarrierCombinations)

	// carrier -> distribution center -> weight tier index -> bool var.
	weightTierVariables := make(map[string]map[string]map[int]mip.Bool)
	for _, combi := range distributionCenterCarrierCombinations {
		_, ok := weightTierVariables[combi.DistributionCenter.DistributionCenterID]
		if !ok {
			weightTierVariables[combi.DistributionCenter.DistributionCenterID] = make(map[string]map[int]mip.Bool)
		}
		_, ok = weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier]
		if !ok {
			weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier] = make(map[int]mip.Bool)
		}
		weightTiersLength :=
			len(i.CarrierDeliveryCosts[combi.DistributionCenter.DistributionCenterID][combi.Carrier]["weight_tiers"])
		for k := 0; k < weightTiersLength+1; k++ {
			weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier][k] = m.NewBool()
		}
	}

	// multimap for the delivery costs for each distribution center carrier
	// combination.
	deliveryCosts := model.NewMultiMap(
		func(...carrier) mip.Float {
			return m.NewFloat(0.0, 100000.0)
		}, distributionCenterCarrierCombinations)

	// We want to minimize the costs for fulfilling the order.
	m.Objective().SetMinimize()

	// Fulfilment constraint -> ensure all items are assigned.
	for _, item := range i.Items {
		fulfillment := m.NewConstraint(
			mip.Equal,
			item.Quantity,
		)
		for _, a := range itemToAssignments[item.ItemID] {
			fulfillment.NewTerm(float64(a.Quantity), x.Get(a))
		}
	}

	// Carrier capacity constraint -> consider the carrier capacities in the
	// solution; carrier capacity is considered in volume.
	for dcID, dc := range distributionCenterToCarrierToAssignments {
		for cID, list := range dc {
			carrier := m.NewConstraint(
				mip.LessThanOrEqual,
				i.CarrierCapacities[dcID][cID],
			)
			for _, as := range list {
				carrier.NewTerm(as.Item.UnitVolume*as.Item.Quantity, x.Get(as))
			}
		}
	}

	/* Inventory constraint -> Consider the inventory of each item at the
	distribution centers. */
	for _, item := range i.Items {
		for _, dc := range i.DistributionCenters {
			inventory := m.NewConstraint(
				mip.LessThanOrEqual,
				float64(dc.Inventory[item.ItemID]),
			)
			for _, a := range itemToAssignments[item.ItemID] {
				if a.DistributionCenter.DistributionCenterID == dc.DistributionCenterID {
					inventory.NewTerm(float64(a.Quantity), x.Get(a))
				}
			}
		}
	}

	/* carton computation -> look at every distribution center and accumulate
	the volume of all the assigned items, use the carton volume from the input to
	compute the number of cartons that are necessary.
	volume computation -> compute the volume for each distribution center -
	carrier combination.
	weight computation -> compute the weight for each
	distribution center - carrier combination. */
	for _, dc := range distributionCenterCarrierCombinations {
		cartonConstr := m.NewConstraint(
			mip.Equal,
			0.0,
		)
		cartonConstr.NewTerm(-1, cartons.Get(dc))

		volumeConstr := m.NewConstraint(
			mip.Equal,
			0.0,
		)
		volumeConstr.NewTerm(-1, volumes.Get(dc))

		weightConstr := m.NewConstraint(
			mip.Equal,
			0.0,
		)
		weightConstr.NewTerm(-1, weights.Get(dc))

		for _, a := range assignments {
			if a.DistributionCenter.DistributionCenterID == dc.DistributionCenter.DistributionCenterID &&
				a.Carrier == dc.Carrier {
				cartonConstr.NewTerm(a.Item.UnitVolume*float64(a.Quantity)*1/i.CartonVolume, x.Get(a))
				volumeConstr.NewTerm(a.Item.UnitVolume*float64(a.Quantity), x.Get(a))
				weightConstr.NewTerm(a.Item.UnitWeight*float64(a.Quantity), x.Get(a))
			}
		}
	}

	/* dimensional weight computation -> by using the carrier specific
	dimensional weight factor, the dimensional weight of each shipnode carrier
	combination is determined.
	billable weight computation -> computes the billable weight for each
	distribution center carrier combination, which is the max between the actual
	weight and the dimensional weight of that combination. */
	for _, combi := range distributionCenterCarrierCombinations {
		dimWeightConstr := m.NewConstraint(
			mip.Equal,
			0.0,
		)
		dimWeightConstr.NewTerm(1.0, dimensionalWeights.Get(combi))
		dimWeightConstr.NewTerm(-i.CarrierDimensionalWeightFactors[combi.Carrier], volumes.Get(combi))

		/* Due to the fact that the billable weight will be used in the
		objective function and we're trying to minimize cost, the billable weight will
		be either set to the actual weight or to the dimensional weight. */
		billableWeightConstr1 := m.NewConstraint(
			mip.GreaterThanOrEqual,
			0.0,
		)
		billableWeightConstr1.NewTerm(1.0, billableWeights.Get(combi))
		billableWeightConstr1.NewTerm(-1.0, weights.Get(combi))

		billableWeightConstr2 := m.NewConstraint(
			mip.GreaterThanOrEqual,
			0.0,
		)
		billableWeightConstr2.NewTerm(1.0, billableWeights.Get(combi))
		billableWeightConstr2.NewTerm(-1.0, dimensionalWeights.Get(combi))
	}

	/* Only one weight tier -> for each carrier, only a single weight tier can
	be selected. */
	for _, dc := range i.DistributionCenters {
		for c := range i.CarrierDimensionalWeightFactors {
			tiersConstraint := m.NewConstraint(mip.Equal, 1.0)
			weightTiersLength := len(i.CarrierDeliveryCosts[dc.DistributionCenterID][c]["weight_tiers"])
			for k := 0; k < weightTiersLength+1; k++ {
				tiersConstraint.NewTerm(1.0, weightTierVariables[dc.DistributionCenterID][c][k])
			}
		}
	}

	/* Weight tier upper limit -> used to determine actual weight tier of a
	distribution center carrier combination*/
	for _, combi := range distributionCenterCarrierCombinations {
		upperConstraint := m.NewConstraint(mip.LessThanOrEqual, 0.0)
		upperConstraint.NewTerm(1, billableWeights.Get(combi))
		weightTiersLength :=
			len(i.CarrierDeliveryCosts[combi.DistributionCenter.DistributionCenterID][combi.Carrier]["weight_tiers"])
		for k := 0; k < weightTiersLength+1; k++ {
			if k == weightTiersLength {
				upperConstraint.NewTerm(
					-totalWeight,
					weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier][k],
				)
			} else {
				upperConstraint.NewTerm(
					-i.CarrierDeliveryCosts[combi.DistributionCenter.DistributionCenterID][combi.Carrier]["weight_tiers"][k],
					weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier][k],
				)
			}
		}
	}

	/* weight tier lower limit -> used to determine actual weight tier of a
	distribution center carrier combination */
	for _, combi := range distributionCenterCarrierCombinations {
		lowerConstraint := m.NewConstraint(mip.LessThanOrEqual, 0.0)
		weightTiersLength :=
			len(i.CarrierDeliveryCosts[combi.DistributionCenter.DistributionCenterID][combi.Carrier]["weight_tiers"])
		for k := 0; k < weightTiersLength+1; k++ {
			if k == 0 {
				lowerConstraint.NewTerm(0, weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier][k])
			} else {
				lowerConstraint.NewTerm(
					i.CarrierDeliveryCosts[combi.DistributionCenter.DistributionCenterID][combi.Carrier]["weight_tiers"][k-1],
					weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier][k],
				)
			}
		}
		lowerConstraint.NewTerm(-1, billableWeights.Get(combi))
	}

	/* delivery costs constraint -> compute the delivery costs based on the
	selected weight tier for each distribution center and carrier combination */
	for _, combi := range distributionCenterCarrierCombinations {
		costsConstraint := m.NewConstraint(mip.Equal, 0.0)
		costsConstraint.NewTerm(1, deliveryCosts.Get(combi))
		weightTiersLength :=
			len(i.CarrierDeliveryCosts[combi.DistributionCenter.DistributionCenterID][combi.Carrier]["weight_tiers"])
		for k := 0; k < weightTiersLength+1; k++ {
			if k == weightTiersLength {
				costsConstraint.NewTerm(
					-i.CarrierDeliveryCosts[combi.DistributionCenter.DistributionCenterID][combi.Carrier]["weight_rates"][k-1],
					weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier][k],
				)
			} else {
				costsConstraint.NewTerm(
					-i.CarrierDeliveryCosts[combi.DistributionCenter.DistributionCenterID][combi.Carrier]["weight_rates"][k],
					weightTierVariables[combi.DistributionCenter.DistributionCenterID][combi.Carrier][k],
				)
			}
		}
	}

	/* objective function = handling costs + delivery costs */
	/* handling costs: cost is based on number of cartons that need to be
	handled at a distribution center */
	/* delivery costs: cost is based on number of cartons that need to be
	transported */
	for _, combination := range distributionCenterCarrierCombinations {
		m.Objective().NewTerm(1.0, deliveryCosts.Get(combination))
		m.Objective().NewTerm(combination.DistributionCenter.HandlingCost, cartons.Get(combination)) // handling costs
	}

	// We create a solver using the 'highs' provider.
	solver, err := mip.NewSolver("highs", m)
	if err != nil {
		return schema.Output{}, err
	}

	// We create the solve options we will use.
	solveOptions := mip.SolveOptions{}

	// Limit the solve to a maximum duration.
	solveOptions.Duration = opts.Solve.Duration
	// Set the relative gap to 0% (highs' default is 5%).
	solveOptions.MIP.Gap.Relative = 0.0

	// Set verbose level to see a more detailed output.
	solveOptions.Verbosity = mip.Off

	solution, err := solver.Solve(solveOptions)
	if err != nil {
		return schema.Output{}, err
	}

	output, err := format(solution, x, assignments,
		distributionCenterCarrierCombinations, cartons, volumes,
		dimensionalWeights, weights, billableWeights,
		weightTierVariables, deliveryCosts,
	)
	if err != nil {
		return schema.Output{}, err
	}

	return output, nil
}

type oflSolution struct {
	Assignments        []assignmentOutput     `json:"assignments"`
	Cartons            map[string]float64     `json:"cartons"`
	Status             string                 `json:"status"`
	Value              float64                `json:"value"`
	Volumes            map[string]float64     `json:"volumes"`
	DimensionalWeights map[string]float64     `json:"dimensional_weights"`
	Weights            map[string]float64     `json:"weights"`
	BillableWeights    map[string]float64     `json:"billable_weights"`
	WeightTiers        map[string]map[int]int `json:"weight_tiers"`
	DeliveryCosts      map[string]float64     `json:"delivery_costs"`
}

type customResultStatistics struct {
	DeliveryCosts float64 `json:"delivery_costs"`
	HandlingCosts float64 `json:"handling_costs"`
}

func format(
	solution mip.Solution,
	x model.MultiMap[mip.Bool, assignment],
	assignments []assignment,
	carriers []carrier,
	cartons model.MultiMap[mip.Float, carrier],
	volumes model.MultiMap[mip.Float, carrier],
	dimensionalWeights model.MultiMap[mip.Float, carrier],
	weights model.MultiMap[mip.Float, carrier],
	billableWeights model.MultiMap[mip.Float, carrier],
	weightTierVariables map[string]map[string]map[int]mip.Bool,
	deliveryCosts model.MultiMap[mip.Float, carrier],
) (output schema.Output, err error) {
	o := schema.Output{}

	o.Version = schema.Version{
		Sdk: sdk.VERSION,
	}

	stats := statistics.NewStatistics()
	result := statistics.Result{}
	run := statistics.Run{}

	t := round(solution.RunTime().Seconds())
	run.Duration = &t
	result.Duration = &t

	oflSolution := oflSolution{}
	oflSolution.Status = "infeasible"

	if solution != nil && solution.HasValues() {
		if solution.IsOptimal() {
			oflSolution.Status = "optimal"
		} else {
			oflSolution.Status = "suboptimal"
		}

		oflSolution.Value = round(solution.ObjectiveValue())
		val := statistics.Float64(round(solution.ObjectiveValue()))
		result.Value = &val

		assignmentList := make([]assignmentOutput, 0)
		for _, assignment := range assignments {
			if solution.Value(x.Get(assignment)) > 0.5 {
				ao := assignmentOutput{
					ItemID:               assignment.Item.ItemID,
					Quantity:             assignment.Quantity,
					DistributionCenterID: assignment.DistributionCenter.DistributionCenterID,
					CarrierID:            assignment.Carrier,
				}
				assignmentList = append(assignmentList, ao)
			}
		}

		oflSolution.Assignments = assignmentList

		totalDeliveryCosts := 0.0
		totalHandlingCosts := 0.0

		oflSolution.Cartons = make(map[string]float64)
		oflSolution.Volumes = make(map[string]float64)
		oflSolution.DimensionalWeights = make(map[string]float64)
		oflSolution.Weights = make(map[string]float64)
		oflSolution.BillableWeights = make(map[string]float64)
		oflSolution.WeightTiers = make(map[string]map[int]int)
		oflSolution.DeliveryCosts = make(map[string]float64)
		for _, c := range carriers {
			cs := solution.Value(cartons.Get(c))
			v := solution.Value(volumes.Get(c))
			dw := solution.Value(dimensionalWeights.Get(c))
			w := solution.Value(weights.Get(c))
			bw := solution.Value(billableWeights.Get(c))
			delc := solution.Value(deliveryCosts.Get(c))
			handc := c.DistributionCenter.HandlingCost * cs

			totalDeliveryCosts += delc
			totalHandlingCosts += handc

			oflSolution.Cartons[c.DistributionCenter.DistributionCenterID+"-"+c.Carrier] = cs
			oflSolution.Volumes[c.DistributionCenter.DistributionCenterID+"-"+c.Carrier] = v
			oflSolution.DimensionalWeights[c.DistributionCenter.DistributionCenterID+"-"+c.Carrier] = dw
			oflSolution.Weights[c.DistributionCenter.DistributionCenterID+"-"+c.Carrier] = w
			oflSolution.BillableWeights[c.DistributionCenter.DistributionCenterID+"-"+c.Carrier] = bw
			oflSolution.DeliveryCosts[c.DistributionCenter.DistributionCenterID+"-"+c.Carrier] = delc
			oflSolution.WeightTiers[c.DistributionCenter.DistributionCenterID+"-"+c.Carrier] = make(map[int]int)
			for key, tier := range weightTierVariables[c.DistributionCenter.DistributionCenterID][c.Carrier] {
				oflSolution.WeightTiers[c.DistributionCenter.DistributionCenterID+"-"+c.Carrier][key] = int(solution.Value(tier))
			}
		}

		o.Solutions = append(o.Solutions, oflSolution)

		customResultStatistics := customResultStatistics{
			DeliveryCosts: round(totalDeliveryCosts),
			HandlingCosts: round(totalHandlingCosts),
		}

		result.Custom = customResultStatistics

		stats.Result = &result
		stats.Run = &run
		o.Statistics = stats
	} else {
		return output, errors.New("no solution found")
	}

	return o, nil
}

func round(value float64) float64 {
	precision := 2
	ratio := math.Pow(10, float64(precision))
	round := math.Round(value*ratio) / ratio

	return round
}
