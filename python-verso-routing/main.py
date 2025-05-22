import os

import nextmv
import requests
from visuals import create_visuals

# from visuals import create_visuals

# Read the input from stdin.
input = nextmv.load_local()

options = nextmv.Options(
    nextmv.Parameter(
        "details", bool, True, "Print details to logs. Default true.", False
    ),
)

# Load vroom api key from secrets collection
VROOM_API_KEY = os.getenv("VROOM_API_KEY")
vroom_api_url = f"https://api.verso-optim.com/vrp/v1/solve?api_key={VROOM_API_KEY}"
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(vroom_api_url, headers=headers, json=input.data)
    response.raise_for_status()
    vroom_result = response.json()
    nextmv.log(f"VROOM API call successful: {vroom_result}")
except requests.exceptions.RequestException as e:
    nextmv.log(f"Error calling VROOM API: {e}")
    vroom_result = None

solution = vroom_result if vroom_result else None

#######

assets = create_visuals(solution)

# pull summary of solution into statistics
summary = solution.get("summary", {})

# extract polylines and convert to geojson so we can view the map

# Write output and statistics.
output = nextmv.Output(
    solution=solution,
    statistics=nextmv.Statistics(
        result=nextmv.ResultStatistics(
            value=summary.get("cost"),
            custom=summary,
        ),
    ),
    assets=[assets],
)
nextmv.write(output)
