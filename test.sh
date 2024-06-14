#!/bin/bash

set -euo pipefail

DIRS=()

# DIRS+=("knapsack-pyomo input.json")
# DIRS+=("shift-assignment-pyomo input.json")
# DIRS+=("shift-planning-pyomo input.json")

DIRS+=("demand-forecasting-ortools input.json")
DIRS+=("routing-ortools input.json")
DIRS+=("xpress input.json")
DIRS+=("facility-location-ampl input.json")
DIRS+=("knapsack-ortools inputs/input.json")
DIRS+=("cost-flow-ortools input.json")
DIRS+=("price-optimization-ampl input.json")
DIRS+=("shift-planning-ortools input.json")
DIRS+=("knapsack-ampl input.json")
DIRS+=("shift-assignment-ortools input.json")

DIRS+=("knapsack-ortools-csv input.json")
DIRS+=("knapsack-gurobi input.json")

# Test push and run apps
# for i in "${DIRS[@]}"; do
#     IFS=' ' read dir input <<< $i
#     echo "Running $dir with input $input"
#     cd $dir
#     nextmv app push -a test
#     nextmv app run -a test -i $input -w
#     cd ..
# done

# Get version of apps
for i in "${DIRS[@]}"; do
    IFS=' ' read dir input <<< $i
    cd $dir
    VERSION=$(cat VERSION)
    echo "$dir=$VERSION"
    cd ..
done
