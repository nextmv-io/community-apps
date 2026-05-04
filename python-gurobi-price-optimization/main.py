import json
import os
import time
from typing import Any

import gurobipy as gp
import nextmv
import plotly.express as px
import plotly.graph_objects as go
from gurobipy import GRB


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving avocado price optimization problem:")
    nextmv.log(f"  - regions: {len(loaded_input.data.get('regions', []))}")
    nextmv.log(f"  - supply: {options.supply}")
    nextmv.log(f"  - duration: {options.duration}")

    solution, metrics, assets = solve(loaded_input, options)
    nextmv.write(solution=solution, metrics=metrics, options=options, assets=assets)


def solve(loaded_input: nextmv.Input, options: nextmv.Options) -> tuple[dict[str, Any], dict[str, Any], list[nextmv.Asset]]:
    """Solves the avocado price optimization problem and returns the solution, metrics, and assets."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    data = loaded_input.data
    B = options.supply  # total amount of avocado supply

    # Creates the environment.
    env = gp.Env(empty=True)

    # Read the license file, if available.
    if os.path.isfile("gurobi.lic"):
        env.readParams("gurobi.lic")

    # Creates the model.
    env.start()
    m = gp.Model(env=env)
    m.Params.TimeLimit = options.duration

    # Sets and parameters
    R = data["regions"]  # set of all regions

    peak_or_not = data["peak"]  # 1 if it is the peak season; 0 if isn't
    year = data["year"]

    c_waste = data["cost_per_wasted_product"]  # the cost ($) of wasting an avocado
    c_transport = data["transport_costs"]  # the cost of transporting an avocado

    # Get the lower and upper bounds from the dataset for the price and the number of products to be stocked
    a_min = data["minimum_product_price"]  # minimum avocado price in each region
    a_max = data["maximum_product_price"]  # maximum avocado price in each region
    b_min = data["minimum_product_allocations"]  # minimum number of avocados allocated to each region
    b_max = data["maximum_product_allocations"]  # maximum number of avocados allocated to each region

    p = m.addVars(R, name="p", lb=a_min, ub=a_max)  # price of avocados in each region
    x = m.addVars(R, name="x", lb=b_min, ub=b_max)  # quantity supplied to each region
    s = m.addVars(R, name="s", lb=0)  # predicted amount of sales in each region for the given price
    w = m.addVars(R, name="w", lb=0)  # excess wastage in each region

    # Demand function based on regression coefficients
    d = {
        r: (
            data["coefficients"]["Intercept"]
            + data["coefficients"]["price"] * p[r]
            + data["coefficients"][f"C(region)[T.{r}]" ]
            + data["coefficients"]["year_index"] * (year - 2015)
            + data["coefficients"]["peak"] * peak_or_not
        )
        for r in R
    }

    m.setObjective(sum(p[r] * s[r] - c_waste * w[r] - c_transport[r] * x[r] for r in R))
    m.ModelSense = GRB.MAXIMIZE

    m.addConstr(sum(x[r] for r in R) == B)
    m.addConstrs((s[r] <= x[r] for r in R))
    m.addConstrs((s[r] <= d[r] for r in R))
    m.addConstrs((w[r] == x[r] - s[r] for r in R))
    m.Params.NonConvex = 2
    m.optimize()

    # Build solution
    solution_data = []
    for r in R:
        solution_data.append(
            {
                "region": r,
                "price": round(p[r].X, 2),
                "allocated": round(x[r].X, 8),
                "sold": round(s[r].X, 8),
                "wasted": round(w[r].X, 8),
                "predicted_demand": round(
                    data["coefficients"]["Intercept"]
                    + data["coefficients"]["price"] * p[r].X
                    + data["coefficients"][f"C(region)[T.{r}]" ]
                    + data["coefficients"]["year_index"] * (year - 2015)
                    + data["coefficients"]["peak"] * peak_or_not,
                    8,
                ),
            }
        )

    # Create visualization
    fig = px.scatter(
        solution_data,
        x="price",
        y="sold",
        color="region",
        size="sold",  # Size based on sold quantity
        size_max=15,  # Adjust for desired size of markers
        title="Avocado Sales and Waste by Region",
        labels={"price": "Price per avocado ($)", "sold": "Number of avocados sold (millions)"},
    )

    colors = px.colors.qualitative.Plotly  # Use a color palette from Plotly
    region_colors = {region: colors[i % len(colors)] for i, region in enumerate(R)}

    wasted_data = [{"price": item["price"], "wasted": item["wasted"], "region": item["region"]} for item in solution_data]
    fig.add_trace(
        go.Scatter(
            x=[item["price"] for item in wasted_data],
            y=[item["wasted"] for item in wasted_data],
            mode="markers",
            marker=dict(symbol="x", size=10, color=[region_colors[item["region"]] for item in wasted_data]),
            name="Wasted",
            showlegend=False,  # Hide legend for wasted points
        )
    )

    fig.update_layout(
        yaxis_range=[0, max(item["sold"] for item in solution_data) * 1.2],
        xaxis_range=[0.5, 2.5],
        legend=dict(x=1.05, y=0.5),  # Adjust legend position
    )

    json_plot = fig.to_json()

    # Build metrics
    metrics = {
        "duration": time.time() - start_time,
        "solve_duration": m.Runtime,
        "objective_value": m.ObjVal,
        "status": m.Status,
        "variables": m.NumVars,
        "constraints": m.NumConstrs,
        "total_waste": sum(w[r].X for r in R),
    }

    solution = {"regions": solution_data}

    # Build assets
    assets = [
        nextmv.Asset(
            name="Avocado price optimization visualization",
            content_type="json",
            visual=nextmv.Visual(
                visual_schema=nextmv.VisualSchema.PLOTLY,
                visual_type="custom-tab",
                label="Visualization",
            ),
            content=[json.loads(json_plot)],
        )
    ]

    return solution, metrics, assets


if __name__ == "__main__":
    main()
