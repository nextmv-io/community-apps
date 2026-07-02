# Nextmv-maxindset
An application for solving the maximum independent set problem

Given an undirect graph $G(V, E)$, the goal is to find the largest possible subset of vertices $I \subset V$ such that no two vertices in $I$ are adjacent.

In this implementation, pure Python is used without need for requirements specification.

## Heuristics
To solve this problem, two heuristics are proposed:
- Greedy algorithm: chooses the next element by 'degree'
- Random choice (with multistart): Chooses randomly a feasible element from the ground set at each step

## Options
When executing the solver via `main.py` you can specify the algorithm via cmd line and also the number of iterations in case of random choice with multistart.

The arguments accepted are:
- `-input`: Path to input file (by default considers `stdin`)
- `-output`: Path to output file (by default considers `stdout`)
- `-algorithm`: Either `random` or `greedy` (by default considers `greedy`)
- `-maxiter`: The number of iterations in case of random choice with multistart (by default considers `1`)
- `-seed`: The random seed for random choice with multistart (by default considers `None`)

## Input file
The expected input file is a json with field "edges" which should be a list of lists (pairs) of edges from the graph.

```json
{
    "edges": [
        [0, 1],
        [2, 1],
        [3, 0]
    ]
}
```
