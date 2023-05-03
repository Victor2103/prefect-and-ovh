# Import the necessary libraries
import ovh
from prefect import flow, task, variables
from prefect.runtime import flow_run, task_run
import json
import datetime

import os
from dotenv import load_dotenv
load_dotenv(".env")


def generate_task_name():
    flow_name = flow_run.flow_name
    task_name = task_run.task_name

    parameters = task_run.parameters
    name = parameters["name"]
    date = datetime.datetime.utcnow()

    return f"{flow_name}-{task_name}-with-{name}-on-{date}"


def generate_flow_name():
    flow_name = flow_run.flow_name

    parameters = flow_run.parameters
    name = parameters["name"]
    date = datetime.datetime.utcnow()

    return f"{flow_name}-with-{name}-on-{date}"


# Define the task to create a client for your public Cloud.
@task(name="init_client-ovh",
      task_run_name=generate_task_name)
def init_ovh(name):
    ovh_client = ovh.Client(
        endpoint=os.getenv("APP_ENDPOINT"),
        application_key=os.getenv("APP_KEY"),
        application_secret=os.getenv("APP_SECRET"),
        consumer_key=os.getenv("CONSUMER_KEY"),
    )
    return ovh_client

# Define the task to get all of your notebook


@task(name="get_infos",
      task_run_name=generate_task_name)
def get_project_infos(client, project_uuid, name: str):
    result = client.get(
        '/cloud/project/'+str(project_uuid))
    print(json.dumps(result, indent=4))

# Define the flow to run on prefect


# Define the flow to run on prefect
@flow(flow_run_name=generate_flow_name)
def display_project_infos(name: str):

    project_uuid = variables.get(
        "Project UUID", default=os.getenv("PROJECT_ID"))

    # Create the OVHcloud client
    client = init_ovh(name="victor")
    # This task print all your Public Cloud project infos
    get_project_infos(client=client, project_uuid=project_uuid, name="victor")


display_project_infos(name="victor")
