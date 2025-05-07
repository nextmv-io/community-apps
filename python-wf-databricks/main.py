# Standard library imports
import json

# Third-party imports
import nextmv
from databricks.sdk import WorkspaceClient
from nextpipe import FlowSpec, needs, step

# Option to pass a Databricks job ID to run
options = nextmv.Options(
    nextmv.Option("db_job_id", str, default="1234567890"),
)


# >>> Workflow definition
class DecisionFlow(FlowSpec):
    @step
    def create_db_run(_):
        """Creates the run on Databricks."""

        db_job_id = options.db_job_id

        # Authenticate (assumes DATABRICKS_HOST and DATABRICKS_TOKEN env vars
        # are set as Nextmv secrets)
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
        nextmv.log(f"Run tasks: {run.tasks}")
        return run.tasks[0].run_id

    @needs(predecessors=[create_db_run])
    @step
    def return_db_result(run_id: str):
        """Gets the result of the run."""
        # Authenticate (assumes DATABRICKS_HOST and DATABRICKS_TOKEN env vars
        # are set as Nextmv secrets)
        w = WorkspaceClient()
        # Get the task run ID
        run_output = w.jobs.get_run_output(run_id=run_id)
        nextmv.log(f"Getting output for DB task: {run_id}")
        # Get the json output from the task
        nextmv_output = run_output.notebook_output.result
        nextmv.log("Adding DB task run ID to Nextmv output")
        result = json.loads(nextmv_output)
        result["statistics"]["result"]["custom"]["db_task_run_id"] = run_id
        result["statistics"]["result"]["custom"]["db_job_id"] = options.db_job_id
        return result

    # You can add more steps here to enhance the result.


def main():
    # There is no input for this workflow
    # If you need to call a Nextmv App, use the following:
    # client = cloud.Client(api_key=os.getenv("NEXTMV_API_KEY"))

    # Run workflow
    flow = DecisionFlow("DecisionFlow", input=None)
    flow.run()
    result = flow.get_result(flow.return_db_result)
    # Write out the result
    nextmv.write(result)


if __name__ == "__main__":
    main()
