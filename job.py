# Import the libraries
# Import the prefect libraries in python
from prefect import flow, task
from prefect_email import EmailServerCredentials, email_send_message
import time
import initClient
import containerS3

# Import error if the client
from botocore.exceptions import ClientError
# from prefect.blocks.notifications import SlackWebhook

from dotenv import load_dotenv
import os

# Load environments variables
load_dotenv(".env")

# Function to send an email to the user with the state of the notebook.
# You need to create a block with your email credentials on prefect cloud.
# The name of my block here is email-block


def email(state_job, exit_code, id_job, name_job):
    email_credentials_block = EmailServerCredentials.load("email-block")
    line_1 = f"Your job with the name {name_job} is finished ! \n"
    line_2 = f"He is in state {state_job}. \n"
    line_3 = f"The id of the job is {id_job}. \n"
    line_4 = f"He has return exit code {exit_code}."
    message = line_1+line_2+line_3+line_4
    subject = email_send_message.with_options(name="send email ").submit(
        email_server_credentials=email_credentials_block,
        subject="Your job via prefect",
        msg=message,
        email_to="victor.vitcheff@ovhcloud.com",
    )
    return (subject)

# Define the task to launch a job


@task
def launch_job(client, bucket_name, region_job, alias_s3, docker_image, name_job, cpu):
    job_creation_params = {
        "image": docker_image,
        "region": region_job,
        "volumes": [
            {
                "dataStore": {
                    "alias": alias_s3,
                    "container": bucket_name,
                    "prefix": ""
                },
                "mountPath": "/workspace/my_data",
                "permission": "RW",
                "cache": False
            }
        ],
        "name": name_job,
        "unsecureHttp": False,
        "resources": {
            "cpu": cpu,
            "flavor": "ai1-1-cpu"
        },
        "command": [
            "bash", "-c", "pip install -r ~/my_data/requirements.txt && python3 ~/my_data/train-first-model.py"
        ],
        "sshPublicKeys": []
    }
    result = client.post(
        f"/cloud/project/{os.getenv('PROJECT_ID')}/ai/job", **job_creation_params)
    return (result)


@task
def wait_state(client, id):
    wait = True
    while wait:
        res = client.get(
            f"/cloud/project/{os.getenv('PROJECT_ID')}/ai/job/{id}")
        status = res['status']['state']
        if (status == "DONE"):
            name = res['spec']['name']
            exitCode = res['status']['exitCode']
            wait = False
        else:
            time.sleep(60)
    return (name, exitCode, status)


# Flow to create an S3 bucket and upload files in it
@flow
def test():
    # Run the first task
    client = initClient.init_s3()
    bucket_name = "python-eae22d77-77e6-4db0-a4d4-f80831b0fa3a"
    # Run the second task
    containerS3.create_bucket(bucket_name=bucket_name,
                              client=client, region="gra")
    files = ["my-dataset.zip", "train-first-model.py", "requirements.txt"]
    # Run the third task
    res = containerS3.upload_data(
        files=files, bucket=bucket_name, client=client)
    if res == True:
        # Run the fourth task
        containerS3.list_bucket_objects(bucket=bucket_name, client=client)
    else:
        raise Exception("Sorry, we can't upload your data")
    return client

# Flow to launch an AI notebook link to the bucket created before


# Flow to test if the ovh API credentials are valid


@flow
def test_credentials():
    ovh_client = initClient.init_ovh()
    return ovh_client.get('/me')['firstname']

# Define the flow to launch the job


@flow
def job():
    ovh_client = initClient.init_ovh()
    docker_image = "ovhcom/ai-training-pytorch:1.8.1"
    region_job = "GRA"
    region_s3 = "S3GRA"
    bucket_name = "python-eae22d77-77e6-4db0-a4d4-f80831b0fa3a"
    name_job = "prefect"
    cpu = 1
    res = launch_job(client=ovh_client,
                     bucket_name=bucket_name,
                     region_job=region_job,
                     alias_s3=region_s3,
                     docker_image=docker_image,
                     name_job=name_job,
                     cpu=cpu)
    name, exitCode, status = wait_state(client=ovh_client, id=res["id"])
    email(state_job=status,
          exit_code=exitCode,
          id_job=res["id"],
          name_job=name)


# Run the flow for the data container and data
# print("Welcome", test(),
#      "Your data has been added in a S3 bucket")

# Run the flow for the job creation
job()

# print("Welcome ",test_credentials())
