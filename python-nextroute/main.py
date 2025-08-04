import nextmv
import nextroute


def main() -> None:
    """Entry point for the program."""

    parameters = [
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
    ]

    default_options = nextroute.Options()
    for name, default_value in default_options.to_dict().items():
        parameters.append(nextmv.Option(name.lower(), type(default_value), default_value, name, False))

    options = nextmv.Options(*parameters)

    input = nextmv.load(options=options, path=options.input)

    nextmv.log("Solving vehicle routing problem:")
    nextmv.log(f"  - stops: {len(input.data.get('stops', []))}")
    nextmv.log(f"  - vehicles: {len(input.data.get('vehicles', []))}")

    model = DecisionModel()
    output = model.solve(input)
    nextmv.write(output, path=options.output)


class DecisionModel(nextmv.Model):
    def solve(self, input: nextmv.Input) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        nextroute_input = nextroute.schema.Input.from_dict(input.data)
        nextroute_options = nextroute.Options.extract_from_dict(input.options.to_dict())
        nextroute_output = nextroute.solve(nextroute_input, nextroute_options)

        return nextmv.Output(
            options=input.options,
            solution=nextroute_output.solutions[0].to_dict(),
            statistics=nextroute_output.statistics.to_dict(),
        )


if __name__ == "__main__":
    main()
