import os
from typing import Any

import nextmv
import requests
from visuals import create_visuals


def main():
    loaded_input = nextmv.load()
    options = loaded_input.options

    solution, metrics = solve(loaded_input.data, options)

    # Create visuals with geojson for each route
    assets = create_visuals(solution)

    nextmv.write(solution=solution, metrics=metrics, options=options, assets=[assets])


def solve(input_data: dict[str, Any], options: nextmv.Options) -> tuple[dict[str, Any], dict[str, Any]]:
    """Calls the VROOM API to solve the routing problem."""

    # Load vroom api key from secrets collection
    vroom_api_key = os.getenv("VROOM_API_KEY")
    vroom_api_url = f"https://api.verso-optim.com/vrp/v1/solve?api_key={vroom_api_key}"
    headers = {"Content-Type": "application/json"}

    # Call VROOM API to solve the problem
    try:
        response = requests.post(vroom_api_url, headers=headers, json=input_data)
        response.raise_for_status()
        vroom_result = response.json()
        nextmv.log(f"VROOM API call successful: {vroom_result}")
    except requests.exceptions.RequestException as e:
        nextmv.log(f"Error calling VROOM API: {e}")
        vroom_result = None

    solution = vroom_result if vroom_result else {}

    # Pull summary of solution into metrics
    summary = solution.get("summary", {})
    metrics = {
        "cost": summary.get("cost"),
        **summary,
    }

    return solution, metrics


if __name__ == "__main__":
    main()
