from prefect import flow, task
import ovh

from dotenv import load_dotenv
import os
import json

# Load environments variables
load_dotenv(".env")


def init_ovh():
    # Visit https://api.ovh.com/createToken/?GET=/me to get your credentials
    ovh_client = ovh.Client(
        endpoint=os.getenv("APP_ENDPOINT"),
        application_key=os.getenv("APP_KEY"),
        application_secret=os.getenv("APP_SECRET"),
        consumer_key=os.getenv("CONSUMER_KEY"),
    )
    return ovh_client


def get_all_notebook(client):
    result = client.get(
        f'/cloud/project/{os.getenv("PROJECT_ID")}/ai/notebook')
    return (json.dumps(result, indent=4))


print(get_all_notebook(init_ovh()))
