import nextmv

# Read from stdin.
input = nextmv.load_local()
name = input.data["name"]

##### Insert model here

# Print logs that render in the run view in Nextmv Console
nextmv.log(f"Hello, {name}")

# Write output and statistics.
output = nextmv.Output(solution=None, statistics={"message": f"Hello, {name}"})
nextmv.write_local(output)
