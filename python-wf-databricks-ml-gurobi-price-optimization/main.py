import json

import nextmv
import pandas as pd
from databricks.sdk import WorkspaceClient
from nextpipe import FlowSpec, app, needs, step

options = nextmv.Options(
    nextmv.Parameter("db_job_id", str, default="1234567890"),
    nextmv.Parameter(
        name="input",
        param_type=str,
        default="input",
        description="Path to the input data.",
        required=False,
    ),
    nextmv.Parameter(
        name="supply",
        param_type=int,
        default=30,
        description="Total amount of avocado supply.",
        required=False,
    ),
)


# >>> Workflow definition
class DecisionFlow(FlowSpec):
    @step
    def create_db_ml_run(_):
        """Creates the run on Databricks."""

        db_job_id = options.db_job_id

        # Authenticate (assumes DATABRICKS_HOST and DATABRICKS_TOKEN env vars are set as Nextmv secrets)
        w = WorkspaceClient()

        # Make sure the job exists
        try:
            w.jobs.get(db_job_id)
        except Exception as err:
            nextmv.log(f"Databricks job with ID {db_job_id} not found")
            raise Exception(f"Databricks job with ID {db_job_id} not found") from err

        # Run the job
        run = w.jobs.run_now(job_id=db_job_id).result()
        nextmv.log(f"Created DB run with ID: {run.run_id} for job with ID: {db_job_id}")
        run_id = run.tasks[0].run_id
        # Get the task run ID from the first task (if single task)
        run_output = w.jobs.get_run_output(run_id=run_id)
        nextmv.log(f"Getting output for DB task: {run_id}")
        nextmv_output = run_output.notebook_output.result
        nextmv.log("Adding DB task run ID to Nextmv output")
        result = json.loads(nextmv_output)
        result["statistics"]["result"]["custom"]["db_task_run_id"] = run_id
        result["statistics"]["result"]["custom"]["db_job_id"] = options.db_job_id
        return result

    @needs(predecessors=[create_db_ml_run])
    @step
    def prep(input: dict):
        """Prepares the input data."""
        ml_output = input["solution"]
        return ml_output

    @app(
        app_id="avocado-price-optimizer",
        instance_id="staging",
        parameters={"supply": options.supply},
    )
    @needs(predecessors=[prep])
    @step
    def optimize():
        """Optimizes the price and supply of avocados per region."""
        pass

    @needs(predecessors=[optimize, create_db_ml_run])
    @step
    def postprocess(optimize_output: dict, ml_output: dict):
        """Postprocesses the results."""
        tabular = pd.DataFrame(optimize_output.get("solution"))
        opt_stats = optimize_output.get("statistics", {})
        ml_stats = ml_output.get("statistics", {}).get("result", {}).get("custom", {})
        opt_stats["result"]["custom"]["db_ml_task_run_id"] = ml_stats.get("run_id")
        opt_stats["result"]["custom"]["ml_app_run_id"] = ml_stats.get("app_id")
        opt_stats["result"]["custom"]["r2_test"] = ml_stats.get("r2_test")
        opt_stats["result"]["custom"]["r2_full"] = ml_stats.get("r2_full")
        opt_stats["result"]["custom"]["db_ml_job_id"] = options.db_job_id
        output = nextmv.Output(
            output_format=nextmv.OutputFormat.CSV_ARCHIVE,
            options=optimize_output.get("solution", {}).get("options"),
            solution={"solution": tabular.to_dict(orient="records")},
            statistics=opt_stats,
            assets=optimize_output.get("assets", []),
        )
        return output


def main():
    # To load an input, use the following.
    # input = nextmv.load()
    # To acces another Nextmv app, use the following.
    # client = cloud.Client(api_key=os.getenv("NEXTMV_API_KEY"))

    # Run workflow
    flow = DecisionFlow("DecisionFlow", input=None)
    flow.run()
    result = flow.get_result(flow.postprocess)
    # Write out the result
    nextmv.write(result)


if __name__ == "__main__":
    main()
