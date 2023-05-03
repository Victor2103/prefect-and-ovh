import datetime
from prefect.runtime import flow_run, task_run


def generate_task_name():
    task_name = task_run.task_name

    parameters = task_run.parameters
    name = parameters["username"]
    date = datetime.datetime.utcnow()

    return f"{task_name}-by-{name}-on-{date}"


def generate_flow_name():
    flow_name = flow_run.flow_name

    parameters = flow_run.parameters
    name = parameters["username"]
    date = datetime.datetime.utcnow()

    return f"{flow_name}-by-{name}-on-{date}"
