#!/bin/bash
set -euo pipefail

# Switch to the root directory
cd "$(dirname "$0")/.."

# PARAMETERS
# Specify apps to skip (separated by space)
SKIP_APPS="knapsack-ampl knapsack-gurobi"

# Determine all apps to test. These are all non-hidden directories that contain
# a README.md file. We use `find` to search for them and clean the dir to get
# the app name.
COMMUNITY_APPS=$(find . -mindepth 2 -maxdepth 2 -not -path '*/\.*' -name README.md | xargs -n 1 dirname | xargs -n 1 basename)

# Make sure nextmv command is installed & accessible
echo "🐰 Checking nextmv command"
export PATH=$PATH:$HOME/.nextmv
nextmv version

# Iterate over apps.
for APP in $COMMUNITY_APPS; do
    # Skip specific apps.
    if [[ $SKIP_APPS =~ (^|[[:space:]])$APP($|[[:space:]]) ]]; then
        echo "🐰 Skipping community app: $APP"
        continue
    fi
    echo "🐰 Community app: $APP"
    cd $APP

    # Install requirements.txt dependencies if they exist.
    if [ -f requirements.txt ]; then
        echo "🐰 Installing requirements.txt dependencies"
        pip install -r requirements.txt
    fi

    # Extract all commands from the file README.md. A command is made up of
    # lines that are enclosed in a code block. The code block is denoted by
    # opening and closing three backticks. Store the commands in an array.
    # Steps:
    #  - Get README.md via 'cat'
    #  - Delete all new lines via 'tr'
    #  - Extract commands via 'grep' (commands are in '``` ... ```')
    #  - Delete '```' via 'sed'
    #  - Deflate whitespace via 'sed'
    #  - Remove 'bash ' prefix via 'sed'
    #  - Remove '```' via 'sed'
    #  - Remove ' \' via 'sed'
    echo "🐰 Reading commands present in the README.md file"
    COMMANDS=$(cat README.md | tr '\n' ' ' | grep -oP '```.*?```' | sed 's/```//' | sed -r 's/\s+/ /g' | sed 's/bash //' | sed 's/```//' | sed 's/ \\//')

    # Each command is printed on a new line. We want to execute each command
    # separately. To do this, we need to convert the string of commands into an
    # array. We do this by setting the IFS (Internal Field Separator) to a
    # newline. We then iterate over the array of commands and execute each
    # command.
    IFS=$'\n'

    # Iterate over commands.
    for COMMAND in ${COMMANDS[@]}; do
        echo "🐰 Executing command: $COMMAND"
        eval "$COMMAND"

        # Check that the command ran successfully
        if [ $? -ne 0 ]; then
            echo "❌ Command failed"
            exit 1
        else
            echo "✅ Command succeeded"
        fi
    done

    cd ..
done
