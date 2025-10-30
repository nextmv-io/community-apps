import json
import time

import gamspy as gp
import networkx as nx
import numpy as np
import pandas as pd
from gamspy.exceptions import GamspyException


def find_subtours(sol: pd.DataFrame):
    G = nx.Graph()
    G.add_edges_from(list(sol[["n1", "n2"]].itertuples(index=False, name=None)))
    components = list(nx.connected_components(G))

    return [list(comp) for comp in components]


def getPath(sol: pd.DataFrame):
    path = [sol.n1.iloc[0], sol.n2.iloc[0]]

    while path[-1] != path[0]:
        current_node = path[-1]
        previous_node = path[-2]

        connected_rows = sol[(sol.n1 == current_node) | (sol.n2 == current_node)]

        for _, row in connected_rows.iterrows():
            next_node_candidate = row.n1 if row.n2 == current_node else row.n2
            if next_node_candidate != previous_node:
                path.append(next_node_candidate)
                break

    return path


def tspModel(
    nodes_recs: pd.DataFrame, distance_recs: pd.DataFrame, maxnodes: int = 10
) -> tuple[list[pd.DataFrame, float], gp.Model]:
    m = gp.Container()

    nodes = gp.Set(m, name="set_of_nodes", records=nodes_recs["row.city"])

    n1 = gp.Alias(m, name="n1", alias_with=nodes)
    n2 = gp.Alias(m, name="n2", alias_with=nodes)

    i = gp.Set(m, name="i", domain=[n1], description="dynamic subset of nodes")
    j = gp.Alias(m, name="j", alias_with=i)
    k = gp.Alias(m, name="k", alias_with=i)

    edges = gp.Set(m, name="allowed_arcs", domain=[n1, n2])
    distance = gp.Parameter(m, name="distance_matrix", domain=[n1, n2], records=distance_recs)

    i[n1].where[gp.Ord(n1) <= maxnodes] = True
    edges[n1, n2].where[(gp.Ord(n1) > gp.Ord(n2)) & i[n1] & j[n2]] = True

    X = gp.Variable(
        m,
        name="x",
        type="binary",
        domain=[n1, n2],
        description="decision variable - leg of trip",
    )

    objective_function = gp.Sum(edges[i, j], distance[i, j] * X[i, j])

    eq_degree = gp.Equation(m, "eq_degree", domain=[n1])
    eq_degree[k] = gp.Sum(edges[i, k], X[i, k]) + gp.Sum(edges[k, j], X[k, j]) == 2

    if not distance[i, j].records.equals(distance[j, i].records):
        raise Exception("Distance matrix is not symmetric. Quitting!")

    s = gp.Set(
        m,
        "s",
        description="Powerset",
        records=range(1000),
    )

    active_cut = gp.Set(m, "active_cut", domain=[s])
    sn = gp.Set(m, "sn", domain=[s, n1], description="subset_membership")

    eq_dfj = gp.Equation(m, "eq_dfj", domain=[s])

    eq_dfj[active_cut] = (
        gp.Sum(
            gp.Domain(i, j).where[edges[i, j] & (sn[active_cut, i]) & (sn[active_cut, j])],
            X[i, j],
        )
        <= gp.Sum(i.where[sn[active_cut, i]], 1) - 1
    )

    tsp = gp.Model(
        m,
        name="tsp",
        problem="MIP",
        sense=gp.Sense.MIN,
        objective=objective_function,
        equations=[eq_degree, eq_dfj],
    )

    cnt = 0
    MAXCUTS = len(s)
    time_limit = 180
    tot_time = 0
    current_tour = gp.Set(m, "current_tour", domain=[n1])

    while True:
        start = time.time()
        tsp.solve(solver="CPLEX", options=gp.Options(time_limit=time_limit))
        sol = X[...].where[X.l > 0.5].records
        subtours = find_subtours(sol)

        if len(subtours) == 1:
            print("***All illegal subtours are removed. Solution found!***")
            break

        if cnt + len(subtours) > MAXCUTS:
            raise GamspyException(
                f"Found {len(subtours)} illegal subtours, but adding them would exceed the cut limit of {MAXCUTS}."
            )

        for idx, tour in enumerate(subtours, start=cnt):
            current_tour.setRecords(tour)
            sn[idx, current_tour] = True

        cnt += len(subtours)
        print(f"Subtours in current solution: {len(subtours)} | total subtours: {cnt}")
        active_cut[s] = gp.Ord(s) <= cnt
        tot_time += time.time() - start

        if tot_time > time_limit:
            print("Total timelimit reached. Stopping!")
            break

    return [sol, tot_time], tsp


def main():
    def euclidean_distance_matrix(coords):
        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        dist_matrix = np.sqrt(np.sum(diff**2, axis=-1))
        return dist_matrix

    with open(r"germany_cities.json") as fp:
        city_data = json.load(fp)

    city_df = pd.json_normalize(city_data["nodes"])
    dist_mat = euclidean_distance_matrix(city_df[["row.latitude", "row.longitude"]].to_numpy())
    dist_df = pd.DataFrame(dist_mat, index=city_df["row.city"], columns=city_df["row.city"])
    distance_df = dist_df.reset_index().melt(id_vars="row.city", var_name="to_city", value_name="distance")

    sol_list, tsp = tspModel(nodes_recs=city_df, distance_recs=distance_df, maxnodes=20)
    sol, _ = sol_list

    path = getPath(sol=sol)

    print(f"Objective Value = {tsp.objective_value * 100: .2f} km")
    print("Solution path:\n", " -> ".join(path))


if __name__ == "__main__":
    main()
