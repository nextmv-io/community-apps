import os

import nextmv
from nextmv import cloud, local

# Initialize the executable code as a local application.
local_app = local.Application(
    src="."
)  # An app manifest will be created if not provided.

# Use options to choose an action when running this script.
options = nextmv.Options(
    nextmv.Option(name="app_id", option_type=str, default="carwash-sim"),
    nextmv.Option(name="app_name", option_type=str, default="Carwash Simulation"),
    nextmv.Option(name="action", option_type=str),
    nextmv.Option(name="input_dir", option_type=str, default="./input/"),
)

if options.action == "sync" or options.action == "push":
    # Initialize the cloud application.
    api_key = os.environ.get("NEXTMV_API_KEY")
    if api_key is None:
        raise Exception("Please set NEXTMV_API_KEY environment variable")

    client = cloud.Client(api_key=api_key)
    cloud_app = cloud.Application.new(
        client=client,
        id=options.app_id,
        name=options.app_name,
        exist_ok=True,
    )

# Do a local run.
if options.action == "local":
    run_1 = local_app.new_run(input_dir_path=options.input_dir)
    print(run_1)

# Sync local application with cloud application.
if options.action == "sync":
    local_app.sync(target=cloud_app, verbose=True)

# Push to cloud application.
if options.action == "push":
    cloud_app.push(app_dir=".", verbose=True)

# Initialize the local application.
if options.action == "init":
    local_app = local.Application(src=".")
