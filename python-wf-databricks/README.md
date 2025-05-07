# Databricks Job Runner with Nextmv

This Python application integrates Nextmv with Databricks to run and manage
Databricks jobs through a Nextmv workflow system. It provides a streamlined way
to execute Databricks jobs and process their results using Nextmv's workflow
capabilities.

## Prerequisites

- Python 3.x
- Nextmv API key
- Databricks workspace access (with DATABRICKS_HOST and DATABRICKS_TOKEN)
- The following Python packages (specified in `requirements.txt`):
  - nextmv==0.25.0
  - nextpipe==0.1.3
  - pandas==2.2.3
  - databricks-sdk

## Environment Setup

1. Install the required dependencies:

   ```bash
   pip3 install -r requirements.txt
   ```

2. Set up the following environment variables:
   - `NEXTMV_API_KEY`: Your Nextmv API key
   - `DATABRICKS_HOST`: Your Databricks workspace URL
   - `DATABRICKS_TOKEN`: Your Databricks access token

## Usage

The application can be run using the following command:

```bash
python3 main.py --db_job_id=<your-databricks-job-id>
```

### Parameters

- `db_job_id` (required): The ID of the Databricks job you want to execute

## Workflow Steps

The application implements a workflow with two main steps:

1. `create_db_run`:
   - Creates and initiates a run of the specified Databricks job
   - Returns the run ID for tracking

2. `return_db_result`:
   - Retrieves the output from the completed Databricks job
   - Processes the JSON output and adds additional metadata
   - Returns the enhanced result

## Example Notebook: Hello World with Nextmv

The repository includes a sample Databricks notebook (`hello-world-nextmv-app.ipynb`)
that demonstrates how to use Nextmv with Databricks.

### Features

- Integration between Nextmv and Databricks via the Nextmv Python SDK
- Running models on Databricks with results viewable in the Nextmv UI

### Prerequisites for the Notebook

Before running the notebook, you need to set up your Nextmv API Key as a
Databricks managed secret:

```bash

databricks secrets put-secret --json '{
    "scope": "<scope-name>",
    "key": "nextmv-api-key",
    "string_value": "<api-key-secret>"
}'
```

### Required Dependencies

The notebook requires the following Python packages:

- `nextmv[all]`
- `plotly`

### Notebook Structure

1. **Setup and Configuration**
   - Installation of required packages
   - Connection to Nextmv using API key
   - Creation/usage of Nextmv app space

2. **Sample Data Processing**
   - Demonstrates working with input data
   - Shows how to track runs in Nextmv
   - Includes visualization capabilities

### Benefits of Using Nextmv

- View and share results via the Nextmv UI
- Manage and compare multiple versions of your model
- Provide a no-code UI for testing model parameters

To run this notebook, make sure you have the necessary Databricks workspace
access and Nextmv API key configured in your secrets management system.

## Output

The workflow produces a JSON output that includes:

- The original Databricks job output
- Additional metadata:
  - `db_task_run_id`: The Databricks task run ID
  - `db_job_id`: The original Databricks job ID

## Error Handling

The application assumes that the necessary environment variables are set and
that the Databricks job exists and is accessible. Make sure to handle any
potential authentication or permission issues before running the workflow.

## Extending the Workflow

The workflow can be extended by adding more steps to the `DecisionFlow` class.
Each new step should be decorated with `@step` and can specify dependencies
using the `@needs` decorator.
