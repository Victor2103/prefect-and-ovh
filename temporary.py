# Import the necessary libraries
import ovh
from prefect import flow, task, variables
import json
import basePrefect
import initClient

import os
from dotenv import load_dotenv
load_dotenv(".env")


@flow
def test_credentials():
    ovh_client = initClient.init_ovh(username="victor")
    return ovh_client.get('/me')['firstname']


# Define the task to get all of your notebook


@task(name="get_infos",
      task_run_name=basePrefect.generate_task_name)
def get_project_infos(client, projectUuid, username: str):
    result = client.get(
        '/cloud/project/'+str(projectUuid))
    print(json.dumps(result, indent=4))

# Define the flow to run on prefect


# Define the flow to run on prefect
@flow(name="test-prefect-with-OVHcloud", flow_run_name=basePrefect.generate_flow_name)
def testPrefectWithOVHcloud(username: str):

    projectUuid = variables.get(
        "project_uiid", default="<your-project-uuid>")

    # Create the OVHcloud client
    client = initClient.init_ovh(username="victor")
    # This task print all your Public Cloud project infos
    get_project_infos(
        client=client, projectUuid=projectUuid, username="victor")


testPrefectWithOVHcloud(username="victor")
