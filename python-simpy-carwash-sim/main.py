"""
Carwash example. https://simpy.readthedocs.io/en/latest/examples/carwash.html

Covers:

- Waiting for other processes
- Resources: Resource

Scenario:
  A carwash has a limited number of washing machines and defines
  a washing processes that takes some (random) time.

  Car processes arrive at the carwash at a random time. If one washing
  machine is available, they start the washing process and wait for it
  to finish. If not, they wait until they can use one.

"""

import itertools
import random
import json

import simpy
import nextmv
from nextmv import cloud

# List to collect all simulation events
simulation_events = []


# MODIFIED - load manifest and extract options to use in the execution
manifest = cloud.Manifest.from_yaml(".")
options = manifest.extract_options()

# Load data from JSON file
with open("input.json", "r") as f:
    data = json.load(f)

NUM_MACHINES = data.get("NUM_MACHINES")  # Number of machines in the carwash
WASHTIME = options.WASHTIME          # Minutes it takes to wash a car
T_INTER = options.T_INTER      # Create a new car every ~7 minutes

class Carwash:
    """A carwash has a limited number of machines (``NUM_MACHINES``) to
    clean cars in parallel.

    Cars have to request one of the machines. When they got one, they
    can start the washing processes and wait for it to finish (which
    takes ``washtime`` minutes).

    """

    def __init__(self, env, num_machines, washtime):
        self.env = env
        self.machine = simpy.Resource(env, num_machines)
        self.washtime = washtime

    def wash(self, car):
        """The washing processes. It takes a ``car`` processes and tries
        to clean it."""
        yield self.env.timeout(self.washtime)
        pct_dirt = random.randint(50, 99)
        nextmv.log(f"Carwash removed {pct_dirt}% of {car}'s dirt.")
        simulation_events.append({
            "event": "wash_complete",
            "car": car,
            "time": self.env.now,
            "dirt_removed_pct": pct_dirt
        })


def car(env, name, cw):
    """The car process (each car has a ``name``) arrives at the carwash
    (``cw``) and requests a cleaning machine.

    It then starts the washing process, waits for it to finish and
    leaves to never come back ...

    """
    arrival_time = env.now
    nextmv.log(f"{name} arrives at the carwash at {arrival_time:.2f}.")
    simulation_events.append({
        "event": "car_arrival",
        "car": name,
        "time": arrival_time
    })

    with cw.machine.request() as request:
        yield request

        start_time = env.now
        wait_time = start_time - arrival_time
        nextmv.log(f"{name} enters the carwash at {start_time:.2f}.")
        simulation_events.append({
            "event": "wash_start",
            "car": name,
            "time": start_time,
            "wait_time": wait_time
        })

        yield env.process(cw.wash(name))

        departure_time = env.now
        nextmv.log(f"{name} leaves the carwash at {departure_time:.2f}.")
        simulation_events.append({
            "event": "car_departure",
            "car": name,
            "time": departure_time,
            "total_time": departure_time - arrival_time
        })


def setup(env, num_machines, washtime, t_inter):
    """Create a carwash, a number of initial cars and keep creating cars
    approx. every ``t_inter`` minutes."""
    # Create the carwash
    carwash = Carwash(env, num_machines, washtime)

    car_count = itertools.count()

    # Create 4 initial cars
    for _ in range(4):
        env.process(car(env, f'Car {next(car_count)}', carwash))

    # Create more cars while the simulation is running
    while True:
        yield env.timeout(random.randint(t_inter - 2, t_inter + 2))
        env.process(car(env, f'Car {next(car_count)}', carwash))


# Setup and start the simulation
nextmv.log("Carwash simulation starting...")
# Generate random seed if RANDOM_SEED is -1, otherwise use the provided value
seed = random.randint(0, 1000) if options.RANDOM_SEED == -1 else options.RANDOM_SEED
random.seed(seed)  # This helps to reproduce the results
nextmv.log(f"Using random seed: {seed}")

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_MACHINES, WASHTIME, T_INTER))

# Execute!
env.run(until=options.SIM_TIME)
nextmv.log("Carwash simulation completed.")

# Calculate summary statistics
total_cars = len([e for e in simulation_events if e["event"] == "car_arrival"])
completed_cars = len([e for e in simulation_events if e["event"] == "car_departure"])
wait_times = [e["wait_time"] for e in simulation_events if e["event"] == "wash_start"]
total_times = [e["total_time"] for e in simulation_events if e["event"] == "car_departure"]

# Write statistics to statistics.json
statistics_file = "statistics.json"
with open(statistics_file, "w") as stats_f:
    statistics = nextmv.Statistics(
        result=nextmv.ResultStatistics(
            value=completed_cars,  # Using completed cars as the objective value
            custom={
                "total_cars": total_cars,
                "completed_cars": completed_cars,
                "average_wait_time": round(sum(wait_times) / len(wait_times), 2) if wait_times else 0,
                "average_total_time": round(sum(total_times) / len(total_times), 2) if total_times else 0,
                "simulation_time": options.SIM_TIME,
                "num_machines": NUM_MACHINES,
                "random_seed": seed
            },
        ),
    )
    stats_f.write(json.dumps({"statistics": statistics.to_dict()}))

# Restructure events by car
cars_dict = {}
for event in simulation_events:
    car_name = event["car"]
    if car_name not in cars_dict:
        cars_dict[car_name] = {
            "car": car_name,
            "events": []
        }
    cars_dict[car_name]["events"].append({
        "event": event["event"],
        "time": event["time"],
        **{k: v for k, v in event.items() if k not in ["car", "event", "time"]}
    })

# Create output structured by car
output = {
    "cars": list(cars_dict.values())
}

# Write output to JSON file
with open("output.json", "w") as f:
    json.dump(output, f, indent=2)