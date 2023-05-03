# Import the libraries
# Import the prefect libraries in python
from prefect import flow, task
from prefect_email import EmailServerCredentials, email_send_message
import initClient

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


# Task to launch the AI Notebook
@task
def launch_notebook(client, bucket_name):
    notebook_creation_params = {"env": {"editorId": "jupyterlab", "frameworkId": "pytorch", "frameworkVersion": "pytorch1.10.1-py39-cuda10.2-v22-4"}, "envVars": None, "labels": {
        "label": "value"
    }, "name": "prefect-2", "region": "GRA", "resources": {"cpu": 3, "flavor": "ai1-1-cpu"},
        "sshPublicKeys": [], "unsecureHttp": False, "volumes": [{"cache": False, "dataStore": {"alias": "S3GRA", "container": "python-5742b54b-f5c1-4bbf-bca9-0ef4921f282a", "prefix": None}, "mountPath": "/workspace/my_data", "permission": "RW"}]}
    result = client.post(f'/cloud/project/{os.getenv("PROJECT_ID")}/ai/notebook',
                         **notebook_creation_params)
    return result


# Task to get the state of the notebook with argument the response when you ask the ovh API
@task
def get_state_notebook(result):
    status = result['status']['state']
    name = result['spec']['name']
    id = result['id']
    url = result['status']['url']
    return (status, name, id, url)

# Flow to create an S3 bucket and upload files in it
@flow
def test():
    # Run the first task
    client = initClient.init_s3()
    bucket_name = "python-eae22d77-77e6-4db0-a4d4-f80831b0fa3a"
    # Run the second task
    create_bucket(bucket_name=bucket_name, client=client, region="gra")
    files = ["my-dataset.zip", "train-first-model.py", "requirements.txt"]
    # Run the third task
    res = upload_data(files=files, bucket=bucket_name, client=client)
    if res == True:
        # Run the fourth task
        list_bucket_objects(bucket=bucket_name, client=client)
    else:
        raise Exception("Sorry, we can't upload your data")
    return client



@flow
def notebook():
    ovh_client = initClient.init_ovh()
    res = launch_notebook(
        client=ovh_client, bucket_name="python-5742b54b-f5c1-4bbf-bca9-0ef4921f282a")
    state_nb, name_nb, id_nb, url_nb = get_state_notebook(result=res)
    #state_email = email(state_notebook=state_nb, url_notebook=url_nb,
                        #id_notebook=id_nb, name_notebook=name_nb)
    return ("Finished !")


# Run the flow for the data container and data
# print("Welcome", test(),
#      "Your data has been added in a S3 bucket")

# Run the flow for the notebook creation
print(f"Flow notebook {notebook()} !")