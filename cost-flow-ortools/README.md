# Nextmv OR-Tools Python template

This template demonstrates how to solve a minimum cost flow problem
using the open source software suite [OR-Tools][or-tools] using the [integer
optimzation][integer-optimization] interface.

In the minimum cost flow problem, the goal is to find the flow with
the smallest total costs on a network of nodes and edges between those nodes.

There are nodes with a demand of a certain material. In order to fulfill these
demands, other nodes offer a supply of this material. The edges in the network
can be used to transport materials from supply nodes to demand nodes.
Transporting on an edge incurs some cost. While solving the given minimum cost
flow problem, the solver finds the flows of materials between nodes that leads
to the least total cost.

The input defines the nodes of the network with their supply (negative supply
equals a demand) as well as the edges between nodes. The graph doesn't have to
be a complete graph so not every node is connected to every other node.
Furthermore, the input contains information about the capacities of edges as
well as the unit costs to utilize an edge for transportation.

In this case, we're assigning workers to projects. Projects have a demand for
time units and require certain skills. Workers can offer time units and their
skills. Skills between workers and projects have to match in order to being able
to assign a worker to a project. Furthermore, projects have a value associated
with it (e.g. the contract value of that project).

The most important files created are `main.py` and `input.json`.

* `main.py` implements a minimum cost flow solver.
* `input.json` is a sample input file.

Follow these steps to run locally.

1. Make sure that all the required packages are installed:

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the command below to check that everything works as expected:

    ```bash
    python3 main.py -input input.json -output output.json
    ```

1. A file `output.json` should have been created with the min cost
   flow.

## Next steps

* Open `main.py` and read through the comments to understand the model.
* Further documentation, guides, and API references about custom modeling and
  deployment can also be found on our [blog](https://www.nextmv.io/blog) and on
  our [documentation site](https://docs.nextmv.io).
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!

[or-tools]: https://developers.google.com/optimization
[integer-optimization]: https://developers.google.com/optimization/mip
