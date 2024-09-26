import nextmv

# Read the input from stdin.
input = nextmv.load_local()
name = input.data["name"]

##### Insert model here

# Print logs that render in the run view in Nextmv Console.
message = f"Hello, {name}"
nextmv.log(message)

# Write output and statistics.
output = nextmv.Output(
    solution=None,
    statistics=nextmv.Statistics(
        result=nextmv.ResultStatistics(
            value=1.23,
            custom={"message": message},
        ),
    ),
)
nextmv.write_local(output)
