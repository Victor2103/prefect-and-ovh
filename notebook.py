# Import the libraries
# Import the prefect libraries in python
from prefect import flow, task, variables
from prefect_email import EmailServerCredentials, email_send_message
import initClient
import containerS3
import basePrefect

from dotenv import load_dotenv
import os

# Load environments variables
load_dotenv(".env")


# Task to launch the AI Notebook
@task(name="launch-an-ai-notebook",
      task_run_name=basePrefect.generate_task_name)
def launch_notebook(client, bucket_name, username):
    notebook_creation_params = {"env": {"editorId": "jupyterlab", "frameworkId": "pytorch", "frameworkVersion": "pytorch1.10.1-py39-cuda10.2-v22-4"}, "envVars": None, "labels": {
        "label": "value"
    }, "name": "prefect-2", "region": "GRA", "resources": {"cpu": 3, "flavor": "ai1-1-cpu"},
        "sshPublicKeys": [], "unsecureHttp": False, "volumes": [{"cache": False, "dataStore": {"alias": "S3GRA", "container": "python-5742b54b-f5c1-4bbf-bca9-0ef4921f282a", "prefix": None}, "mountPath": "/workspace/my_data", "permission": "RW"}]}
    result = client.post(f'/cloud/project/{os.getenv("PROJECT_ID")}/ai/notebook',
                         **notebook_creation_params)
    return result


# Task to get the state of the notebook with argument the response when you ask the ovh API
@task(name="get-the-state-of-the-notebook",
      task_run_name=basePrefect.generate_task_name)
def get_state_notebook(result, username):
    status = result['status']['state']
    name = result['spec']['name']
    id = result['id']
    url = result['status']['url']
    return (status, name, id, url)

# Flow to create an S3 bucket and upload files in it


@flow(name="create-and-upload-data-in-S3",
      flow_run_name=basePrefect.generate_flow_name)
def createS3(username):
    # Get the username and create a prefect variables to send to the task
    myUsername = variables.get('username', default="marvin")
    # Run the first task
    client = initClient.init_s3(myUsername)
    bucket_name = "python-dc025c22-233c-47fa-8573-92fee45aebc6"
    # Run the second task
    res = containerS3.create_bucket(bucket_name=bucket_name,
                                    client=client, region="gra",
                                    username=myUsername)
    if res == False:
        raise Exception("Sorry, we can't create your bucket")
    files = ["my-dataset.zip", "train-first-model.py", "requirements.txt"]
    # Run the third task
    res = containerS3.upload_data(
        files=files, bucket=bucket_name, client=client,
        username=myUsername)
    if res == False:
        raise Exception("Sorry, we can't upload your data")
    # Run the fourth task
    containerS3.list_bucket_objects(bucket=bucket_name, client=client,
                                    username=myUsername)
    return client


@flow(name="create-and-launch-your-notebook",
      flow_run_name=basePrefect.generate_flow_name)
def notebook(username):
    # Get the username and create a prefect variables to send to the task
    myUsername = variables.get('username', default="marvin")
    ovh_client = initClient.init_ovh(username=myUsername)
    res = launch_notebook(
        client=ovh_client, bucket_name="python-5742b54b-f5c1-4bbf-bca9-0ef4921f282a",
        username=myUsername)
    return (get_state_notebook(result=res, username=myUsername))

# Function to send an email to the user with the state of the notebook.
# You need to create a block with your email credentials on prefect cloud.
# The name of my block here is email-block


@flow(name="send-email-with-details-of-the-notebook",
      flow_run_name=basePrefect.generate_flow_name)
def email(state_notebook, url_notebook, id_notebook, name_notebook, username):
    email_credentials_block = EmailServerCredentials.load("email-block")
    line_1 = f"Your job with the name {name_notebook} is finished ! <br>"
    line_2 = f"He is in state {state_notebook}. <br>"
    line_3 = f"The id of the job is {id_notebook}. <br>"
    line_4 = f"You can access it by clicking <a href={url_notebook}>here</a>."
    message = line_1+line_2+line_3+line_4
    # This is a task
    subject = email_send_message.with_options(name="send-an-email",
                                              task_run_name=f"send-an-email-by-{myUsername}").submit(
        email_server_credentials=email_credentials_block,
        subject="Your notebook via prefect",
        msg=message,
        email_to="victor.vitcheff@ovhcloud.com",
    )
    return (subject)


# Get the username and create a prefect variables to send to the task
myUsername = variables.get('username', default="marvin")

# Run the flow for the data container and data
print("Welcome", createS3(username=myUsername),
      "Your data has been added in a S3 bucket")

# Run the flow for the notebook creation
state_nb, name_nb, id_nb, url_nb = notebook(username=myUsername)

# Run the flow to send the email
state_email = email(state_notebook=state_nb, url_notebook=url_nb,
                    id_notebook=id_nb, name_notebook=name_nb, username=myUsername)
print(state_email)
