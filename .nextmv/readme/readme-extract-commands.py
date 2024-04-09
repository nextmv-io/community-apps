#!/bin/env python

import argparse
import glob
import os
import sys

README_TEST_DIR = ".nextmv/readme"


def parse_args():
    parser = argparse.ArgumentParser(description="Extract commands from README files")
    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        help=f"Update commands in {README_TEST_DIR} instead of testing for diffs",
    )
    return parser.parse_args()


def extract_commands_from_readme(readme_file):
    with open(readme_file) as f:
        lines = f.readlines()
    commands, command, prefix_whitespace = [], None, 0
    for line in lines:
        if line.strip().startswith("```") and command is None:
            prefix_whitespace = len(line) - len(line.lstrip())
            command = []
            continue
        if line.strip().startswith("```") and command is not None:
            commands.append("".join(command).strip())
            command = None
            continue
        if command is not None:
            command.append(line[prefix_whitespace:])
    return commands


def main():
    # Parse command-line arguments
    args = parse_args()

    # Find all app README files
    os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
    readme_files = glob.glob("*/README.md")
    apps = [(os.path.dirname(readme_file), readme_file) for readme_file in readme_files]

    # Read all existing commands for comparison, if not updating
    existing_commands = {}
    if not args.update:
        for app, _ in apps:
            app_dir = os.path.join(README_TEST_DIR, app)
            if not os.path.exists(app_dir):
                continue
            existing_commands[app] = []
            for command_file in glob.glob(f"{app_dir}/*.sh"):
                with open(command_file) as f:
                    existing_commands[app].append(f.read())

    # Extract commands from each README file and save them for testing
    for app, readme_file in apps:
        commands = extract_commands_from_readme(readme_file)
        if not commands:
            print(f"No commands found in {readme_file}", file=sys.stderr)
            continue

        # Make sure app directory exists
        app_dir = os.path.join(README_TEST_DIR, app)
        os.makedirs(app_dir, exist_ok=True)

        # Process commands for this app
        if args.update:
            print(f"Updating commands for app {app}:")
            for c, command in enumerate(commands):
                command_file = os.path.join(app_dir, f"{c}.sh")
                with open(command_file, "w") as f:
                    f.write(command)
                    f.write("\n")
                print(f"  {command_file}")
        else:
            print(f"Testing commands for app {app}:")
            for c, command in enumerate(commands):
                command_file = os.path.join(app_dir, f"{c}.sh")
                if c >= len(existing_commands.get(app, [])):
                    print(f"New command: {command_file}", file=sys.stderr)
                    sys.exit(1)
                with open(command_file) as f:
                    existing_command = f.read()
                if command != existing_command:
                    print(f"Command differs: {command_file}", file=sys.stderr)
                    sys.exit(1)
                print(f"  {command_file}: OK")

    print("Done!")


if __name__ == "__main__":
    main()
