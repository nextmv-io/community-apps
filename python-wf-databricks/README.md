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
  - nextmv==0.20.1
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
