# Import the necessary libraries
import ovh
from prefect import flow, task, variables
import json
import basePrefect

import os
from dotenv import load_dotenv
load_dotenv(".env")


# Define the task to create a client for your public Cloud.
@task(name="init_client-ovh",
      task_run_name=basePrefect.generate_task_name)
def init_ovh(username):
    ovh_client = ovh.Client(
        endpoint=os.getenv("APP_ENDPOINT"),
        application_key=os.getenv("APP_KEY"),
        application_secret=os.getenv("APP_SECRET"),
        consumer_key=os.getenv("CONSUMER_KEY"),
    )
    return ovh_client

# Define the task to get all of your notebook


@task(name="get_infos",
      task_run_name=basePrefect.generate_task_name)
def get_project_infos(client, project_uuid, username: str):
    result = client.get(
        '/cloud/project/'+str(project_uuid))
    print(json.dumps(result, indent=4))

# Define the flow to run on prefect


# Define the flow to run on prefect
@flow(name="test-prefect-with-OVHcloud", flow_run_name=basePrefect.generate_flow_name)
def testPrefectWithOVHcloud(username: str):

    project_uuid = variables.get(
        "Project UUID", default=os.getenv("PROJECT_ID"))

    # Create the OVHcloud client
    client = init_ovh(username="victor")
    # This task print all your Public Cloud project infos
    get_project_infos(
        client=client, project_uuid=project_uuid, username="victor")


testPrefectWithOVHcloud(username="victor")
