import nextmv

if __name__ == "__main__":
    # Read from stdin.
    input = nextmv.load_local()
    name = input.data["name"]

    ##### Insert model here

    # Print logs that render in the run view in Nextmv Console
    nextmv.log(f"Hello, {name}")

    # Write output and statistics to stdout.
    output = nextmv.Output(
        solution=f"Hello, {name}",
        statistics=nextmv.Statistics(
            result=nextmv.ResultStatistics(custom={"length": len(name)}),
        ),
    )
    nextmv.write_local(output)
