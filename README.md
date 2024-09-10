# Nextmv community apps

Pre-built decision apps serving as the base for [Marketplace subscription
apps][subscription-apps]. Each app is standalone and can be executed following
the instructions in each `README`.

Before starting:

1. [Sign up][signup] for a Nextmv account.
1. [Install][installation] the Nextmv Platform.

Visit the [docs][docs] for more information.

## Hello, world

Get started with one of the following apps:

* [go-hello-world]: Get started with Go and the Nextmv Platform.
* [java-hello-world]: Get started with Java and the Nextmv Platform.
* [python-hello-world]: Get started with Python and the Nextmv Platform.

## More apps

These examples are concrete cases of using different languages and solvers in
decision apps that run on the Nextmv Platform.

* [go-highs-knapsack]: Use Go and the HiGHS solver to solve a knapsack problem.
* [go-highs-shiftscheduling]: Use Go and the HiGHS solver to solve a shift
  scheduling problem.
* [go-nextroute]: Use Go and Nextmv’s Nextroute solver to solve a vehicle
  routing problem.
* [python-ampl-knapsack]: Use Python and AMPL to solve a knapsack problem.
* [python-gurobi-knapsack]: Use Python and Gurobi to solve a knapsack problem.
* [python-highs-knapsack]: Use Python and the HiGHS solver to solve a knapsack
  problem.
* [python-ortools-costflow]: Use Python and Google OR-Tools to solve a cost
  flow problem.
* [python-ortools-knapsack]: Use Python and Google OR-Tools to solve a knapsack
  problem.
* [python-ortools-knapsack-multicsv]: Use Python and Google OR-Tools to solve a
  knapsack problem with multiple CSV files.
* [python-ortools-routing]: Use Python and Google OR-Tools to solve a vehicle
  routing problem.
* [python-ortools-shiftassignment]: Use Python and Google OR-Tools to solve a
  shift assignment problem.
* [python-ortools-shiftplanning]: Use Python and Google OR-Tools to solve a
  shift planning problem.
* [python-xpress-knapsack]: Use Python and FICO Xpress to solve a knapsack
  problem.

## Other, more complex, examples

These apps show more complete examples and use cases of different languages and
solvers. Most demonstrate how to use devcontainers to run the app like it would
run on Nextmv Cloud.

* [go-highs-orderfulfillment]: Use Go and the HiGHS solver to solve an order
  fulfillment problem. Demonstrates how to use devcontainers.
* [java-ortools-knapsack]: Use Java and Google OR-Tools to solve a knapsack
  problem. Demonstrates how to use devcontainers.
* [java-ortools-routing]: Use Java and Google OR-Tools to solve a vehicle
  routing problem. Demonstrates how to use devcontainers.
* [python-ampl-facilitylocation]: Use Python and AMPL to solve a facility
  location problem. Demonstrates how to use devcontainers.
* [python-ampl-priceoptimization]: Use Python and AMPL to solve a price
  optimization problem. Demonstrates how to use devcontainers.
* [python-ortools-demandforecasting]: Use Python and Google OR-Tools to solve a
  demand forecasting problem. Demonstrates how to use devcontainers.
* [python-pyomo-knapsack]: Use Python and Pyomo to solve a knapsack problem.
  Demonstrates how to use devcontainers.
* [python-pyomo-shiftassignment]: Use Python and Pyomo to solve a shift
  assignment problem. Demonstrates how to use devcontainers.
* [python-pyomo-shiftplanning]: Use Python and Pyomo to solve a shift planning
  problem. Demonstrates how to use devcontainers.
* [python-pyvroom-routing]: Use Python and Pyvroom to solve a vehicle routing
  problem. Demonstrates how to use devcontainers.

[subscription-apps]: https://nextmv.io/docs/platform/deploy-app/subscription-apps
[installation]: https://nextmv.io/docs/platform/installation
[docs]: https://nextmv.io/docs
[signup]: https://cloud.nextmv.io

[go-hello-world]: ./go-hello-world/README.md
[java-hello-world]: ./java-hello-world/README.md
[python-hello-world]: ./python-hello-world/README.md
[go-highs-knapsack]: ./go-highs-knapsack/README.md
[go-highs-orderfulfillment]: ./go-highs-orderfulfillment/README.md
[go-highs-shiftscheduling]: ./go-highs-shiftscheduling/README.md
[go-nextroute]: ./go-nextroute/README.md
[java-ortools-knapsack]: ./java-ortools-knapsack/README.md
[java-ortools-routing]: ./java-ortools-routing/README.md
[python-ampl-facilitylocation]: ./python-ampl-facilitylocation/README.md
[python-ampl-knapsack]: ./python-ampl-knapsack/README.md
[python-ampl-priceoptimization]: ./python-ampl-priceoptimization/README.md
[python-gurobi-knapsack]: ./python-gurobi-knapsack/README.md
[python-highs-knapsack]: ./python-highs-knapsack/README.md
[python-ortools-costflow]: ./python-ortools-costflow/README.md
[python-ortools-demandforecasting]: ./python-ortools-demandforecasting/README.md
[python-ortools-knapsack]: ./python-ortools-knapsack/README.md
[python-ortools-knapsack-multicsv]: ./python-ortools-knapsack-multicsv/README.md
[python-ortools-routing]: ./python-ortools-routing/README.md
[python-ortools-shiftassignment]: ./python-ortools-shiftassignment/README.md
[python-ortools-shiftplanning]: ./python-ortools-shiftplanning/README.md
[python-pyomo-knapsack]: ./python-pyomo-knapsack/README.md
[python-pyomo-shiftassignment]: ./python-pyomo-shiftassignment/README.md
[python-pyomo-shiftplanning]: ./python-pyomo-shiftplanning/README.md
[python-pyvroom-routing]: ./python-pyvroom-routing/README.md
[python-xpress-knapsack]: ./python-xpress-knapsack/README.md
