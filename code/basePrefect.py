# Import the library to get the exact time
import datetime

# Import the libraries to get the name of the flow_run and the task_run
from prefect.runtime import flow_run, task_run

# Function to generate automatically the task name


def generate_task_name():
    task_name = task_run.task_name

    parameters = task_run.parameters
    name = parameters["username"]
    date = datetime.datetime.utcnow()

    return f"{task_name}-by-{name}-on-{date}"

# Function to generate automatically the flow name


def generate_flow_name():
    flow_name = flow_run.flow_name

    parameters = flow_run.parameters
    name = parameters["username"]
    date = datetime.datetime.utcnow()

    return f"{flow_name}-by-{name}-on-{date}"
