import argparse
import json
import random
from typing import Optional


def instance(n: int, frac: float, seed: Optional[int] = None) -> dict:
    """Creates random instance of undirected graph

    Parameters
    ----------
    n : int
        Number of nodes
    frac : float
        Average connectivity

    seed : Optional[int], optional
        Random generator seed, by default None

    Returns
    -------
    dict
        Data with keys:
        - "nodes" : a list of integers
        - "edges" : a list of lists of integers
        - "n" : number of nodes
        - "e" : number of edges
    """

    # Compute nodes and number of connections
    nodes = list(range(n))
    edges = []
    k = max(1, int(n * n * frac / 2))
    random.seed(seed)

    # No connections if n = 1
    if n == 1:
        k = 0

    # Otherwise include pairs randomly
    while k > 0:
        i, j = random.sample(nodes, 2)
        if [j, i] not in edges:
            edges.append([i, j])
            k = k - 1

    data = {
        "nodes": nodes,
        "edges": edges,
        "n": n,
        "e": len(edges)
    }
    return data


def parse_arguments():
    # Create the parser
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument("n", type=int, help="Number of nodes")
    parser.add_argument("frac", type=float, help="Average fraction of connections created from node")
    parser.add_argument('--seed', type=int, default=None, help="Random seed for reproducibility (optional).")

    # Parse the arguments
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    n, frac, seed = args.n, args.frac, args.seed
    data = instance(n, frac, seed)
    with open(f"n{n}_frac{frac}_s{seed}.json", mode="w", encoding="utf8") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    main()
