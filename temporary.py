# Import the necessary libraries
import ovh
from prefect import flow, task
import json

import os
from dotenv import load_dotenv
load_dotenv(".env")

# Define the task to create a client for your public Cloud.


@task
def init_ovh():
    ovh_client = ovh.Client(
        endpoint=os.getenv("APP_ENDPOINT"),
        application_key=os.getenv("APP_KEY"),
        application_secret=os.getenv("APP_SECRET"),
        consumer_key=os.getenv("CONSUMER_KEY"),
    )
    return ovh_client

# Define the task to get all of your notebook


@task
def get_all_swift_containers(client):
    result = client.get(
        f'/cloud/project/{os.getenv("PROJECT_ID")}/storage')
    return (json.dumps(result, indent=4))

# Define the flow to run on prefect


@flow
def display_swift_containers():
    # Create the OVHcloud client
    client = init_ovh()
    # this flow returns all of your notebook in your public cloud
    return (get_all_swift_containers(client=client))


# Launch your flow and display the result
print(display_swift_containers())
