import nextmv
from visuals import create_visuals

# Read the input from stdin.
input = nextmv.load_local()
name = input.data["name"]

options = nextmv.Options(
    nextmv.Option("details", bool, True, "Print details to logs. Default true.", False),
)

##### Insert model here

# Print logs that render in the run view in Nextmv Console.
message = f"Hello, {name}"
nextmv.log(message)

if options.details:
    detail = "You are", {input.data["distance"]}, " million km from the sun"
    nextmv.log(detail)

assets = create_visuals(name, input.data["radius"], input.data["distance"])

# Write output and statistics.
output = nextmv.Output(
    solution=None,
    statistics=nextmv.Statistics(
        result=nextmv.ResultStatistics(
            value=1.23,
            custom={"message": message},
        ),
    ),
    assets=assets,
)
nextmv.write_local(output)
