import nextmv

input_loader = nextmv.LocalInputLoader()
input = input_loader.load()
name = input.data["name"]

##### Insert model here

# Print logs that render in the run view in Nextmv Console
nextmv.log(f"Hello, {name}")

# Print statistics to the details run view in Nextmv Console
output = nextmv.Output(statistics={"message": f"Hello, {name}"})
output_writer = nextmv.LocalOutputWriter()
output_writer.write(output)
