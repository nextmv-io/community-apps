import nextmv

input = nextmv.load_local()
name = input.data["name"]

##### Insert model here

# Print logs that render in the run view in Nextmv Console
nextmv.log(f"Hello, {name}")

# Print statistics to the details run view in Nextmv Console
output = nextmv.Output(statistics={"message": f"Hello, {name}"})
nextmv.write_local(output)
