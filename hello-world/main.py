import json
import nextmv
import sys

def main():
    # Read input data
    input_data = json.load(sys.stdin)
    name = input_data["name"]

    ##### Insert model here

    # Print logs that render in the run view in Nextmv Console
    print(f"Hello, {name}", file=sys.stderr)

    # Print statistics to the details run view in Nextmv Console
    output = {"statistics": {"message": f"Hello, {name}"}}

    # Give output result
    json.dump(output, fp=sys.stdout)

if __name__ == "__main__":
    main()
