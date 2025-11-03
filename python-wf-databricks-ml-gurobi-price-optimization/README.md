# Avocado Price Optimization with Nextmv and Databricks

This Python application integrates Nextmv with Databricks to create an
end-to-end workflow for avocado price optimization. It combines machine learning
predictions from Databricks with a Gurobi optimization model running on
Nextmv to determine optimal pricing.

The content of this worklflow is based on the [Gurobi example](https://colab.research.google.com/github/Gurobi/modeling-examples/blob/master/price_optimization/price_optimization.ipynb)

## Workflow Prerequisites

- Python 3.11
- Nextmv API key
- Databricks workspace access (with DATABRICKS_HOST and DATABRICKS_TOKEN)
- The Python packages specified in `requirements.txt`

## Environment Setup

1. Install the required dependencies:

   ```bash
   pip3 install -r requirements.txt
   ```

2. Set up the following environment variables:
   - `NEXTMV_API_KEY`: Your Nextmv API key
   - `DATABRICKS_HOST`: Your Databricks workspace URL
   - `DATABRICKS_TOKEN`: Your Databricks access token

## Setup

1. Add the `avocado-ml-regressor` notebook to your Databricks workspace
2. Create a Databricks Workflow with the regressor notebook as a Task
3. Run the `avocado-price-optimizer` notebook once from Databricks
4. Run your workflow locally or push the workflow to a workflow app on Nextmv

## Usage

The application can be run using the following command:

```bash
python3 main.py --db_job_id=<your-databricks-job-id> --supply=<total-avocado-supply>
```

### Parameters

- `db_job_id` (required): The ID of the Databricks job containing the ML model
- `supply` (optional): Total amount of avocado supply (default: 30)
- `input` (optional): Path to the input data (default: "input")

## Workflow Steps

The application implements a workflow with four main steps:

1. `create_db_ml_run`:
   - Creates a run of the avocado-ml-regressor Databricks notebook job
   - Retrieves the ML model predictions
   - Returns the run ID and predictions for tracking

2. `prep`:
   - Processes the ML model output
   - Prepares the ML data for input to the Gurobi optimization

3. `optimize`:
   - Runs the Nextmv optimization model
   - Determines optimal price and supply distribution per region

4. `postprocess`:
   - Combines ML and optimization results
   - Generates final output with enhanced metadata
   - Produces CSV archive with solution

## Example Notebook: Avocado ML Regressor

The repository includes a sample Databricks notebook (`avocado-ml-regressor.ipynb`)
that demonstrates the machine learning component of the workflow. This notebook
should be added as a Task in a Databricks Workflow Job.

### Features

- Integration between Nextmv and Databricks via the Nextmv Python SDK
- Machine learning model for avocado price prediction
- Tracks results to an app that is viewable in the Nextmv UI

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
- `pandas`
- `scikit-learn`

## Output

The workflow produces a CSV that includes:

- Optimal price and supply distribution per region
- ML model performance metrics (R² scores)
- Additional metadata:
  - `ml_app_run_id`: The Nextmv avocado-ml-regressor app run ID
  - `r2_test`: Test set R² score for the avocado regressor
  - `r2_full`: Full dataset R² score for the avocado regressor
  - `db_ml_job_id`: The original Databricks job ID

## Error Handling

The application assumes that the necessary environment variables are set and
that the Databricks job exists and is accessible. Make sure to handle any
potential authentication or permission issues before running the workflow.

## Extending the Workflow

The workflow can be extended by adding more steps to the `DecisionFlow` class.
Each new step should be decorated with `@step` and can specify dependencies
using the `@needs` decorator.
