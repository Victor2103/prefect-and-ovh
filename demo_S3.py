# Import the libraries
# Import the prefect libraries in python
from prefect import flow, task
from prefect_email import EmailServerCredentials, email_send_message

# Import the ovh client and boto3 for s3 storage
import ovh
import boto3

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


def email(state_notebook, url_notebook, id_notebook, name_notebook):
    email_credentials_block = EmailServerCredentials.load("email-block")
    line_1 = f"Your notebook with the name {name_notebook} has been created ! \n"
    line_2 = f"He is in state {state_notebook}. \n"
    line_3 = f"The id of the notebook is {id_notebook}. \n"
    line_4 = f"You can access it on this url : {url_notebook}."
    message = line_1+line_2+line_3+line_4
    subject = email_send_message.with_options(name="send email ").submit(
        email_server_credentials=email_credentials_block,
        subject="Your notebook via prefect",
        msg=message,
        email_to="victor.vitcheff@ovhcloud.com",
    )
    return (subject)


# First task to create an open stack token
@task
def init_ovh():
    # Visit https://api.ovh.com/createToken/?GET=/me to get your credentials
    ovh_client = ovh.Client(
        endpoint=os.getenv("APP_ENDPOINT"),
        application_key=os.getenv("APP_KEY"),
        application_secret=os.getenv("APP_SECRET"),
        consumer_key=os.getenv("CONSUMER_KEY"),
    )
    return ovh_client

# Task to create a botoS3 client


@task
def init_s3():
    # Log in OVHcloud Object Storage with S3 protocol
    # To get credentials, go to Control Panel / Public Cloud / (your project) / Users / (generate S3 credentials)
    # boto3 doc : https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html
    # For the credentials of boto3 use the S3 credentials created on the OVHcloud control pannel
    client = boto3.client(
        's3',
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        endpoint_url=os.getenv("S3_ENDPOINT"),
        region_name=os.getenv("S3_REGION")
    )
    return client


# Task for listing all of your S3 buckets
@task
def list_buckets(client):
    try:
        response = client.list_buckets()
        # Output the bucket names
        print('Existing buckets:')
        for bucket in response['Buckets']:
            print(f'  {bucket["Name"]}')
    except ClientError as error:
        raise ValueError("Unable to List buckets")
    pass


# Task for creating an S3 bucket
@task
def create_bucket(bucket, client):
    try:
        location = {'LocationConstraint': "gra"}
        response = client.create_bucket(
            Bucket=bucket, CreateBucketConfiguration=location)
    except ClientError as error:
        if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            # We grab the message, request ID, and HTTP code to give to customer support
            print('Info : bucket already exist.')
        else:
            raise ValueError("Unable to create bucket")
    return (response)


# Task to list all of the objects inside a bucket
@task
def list_bucket_objects(bucket, client):
    try:
        response = client.list_objects_v2(Bucket=bucket, MaxKeys=10)
        print(response)
    except ClientError as error:
        # Put your error handling logic here
        raise ValueError("Unable to list bucket objects.")
    pass


# Task to upload some files in a S3 bucket
@task
def upload_data(files, bucket, client):
    # Upload a file to an S3 bucket
    # param file: File to upload
    # param bucket: Bucket to upload to
    # return: True if file was uploaded, else False
    for file in files:
        try:
            file = str(file)
            object_name = file
            response = client.upload_file(file, bucket, object_name)
        except ClientError as e:
            return False
    return True

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
    """
    slack_webhook_block = SlackWebhook.load("slack")
    slack_webhook_block.notify(f"Your notebook with the name {name} has been created ! \n")
    slack_webhook_block.notify(f"He is in state {status}")
    slack_webhook_block.notify(f"The id of the notebook is {id}")
    slack_webhook_block.notify(f"You can access it on this url : {url}")
    return "A message has been sent ! "
    """
    return (status, name, id, url)

# Define the task to launch a job
@task
def launch_job(client, bucket_name):
    job_creation_params = {
        "image": "ovhcom/ai-training-pytorch:1.8.1",
        "region": "GRA",
        "volumes": [
            {
                "dataStore": {
                    "alias": "S3GRA",
                    "container": "python-5742b54b-f5c1-4bbf-bca9-0ef4921f282a",
                    "prefix": ""
                },
                "mountPath": "/workspace/my_data",
                "permission": "RW",
                "cache": False
            }
        ],
        "name": "prefect",
        "unsecureHttp": False,
        "resources": {
            "cpu": 1,
            "flavor": "ai1-1-cpu"
        },
        "command": [
            "bash","-c","pip install -r ~/my_data/requirements_job.txt && python3 ~/my_data/train-first-model.py"
        ],
        "sshPublicKeys": []
    }
    result = client.post(
        f"/cloud/project/{os.getenv('PROJECT_ID')}/ai/job", **job_creation_params)
    return (result)

# Flow to create an S3 bucket and upload files in it


@flow
def test():
    ovh_client = init_ovh()
    res = init_s3()
    list_buckets(res)
    bucket_name = "python-5742b54b-f5c1-4bbf-bca9-0ef4921f282a"
    create_bucket(bucket=bucket_name, client=res)
    list_bucket_objects(bucket=bucket_name, client=res)
    files = ["my-dataset.zip", "train-first-model.py", "requirements_job.txt"]
    upload_data(files=files, bucket=bucket_name, client=res)
    list_bucket_objects(bucket=bucket_name, client=res)
    return ovh_client

# Flow to launch an AI notebook link to the bucket created before
@flow
def notebook():
    ovh_client = init_ovh()
    res = launch_notebook(
        client=ovh_client, bucket_name="python-5742b54b-f5c1-4bbf-bca9-0ef4921f282a")
    state_nb, name_nb, id_nb, url_nb = get_state_notebook(result=res)
    state_email = email(state_notebook=state_nb, url_notebook=url_nb,
                        id_notebook=id_nb, name_notebook=name_nb)
    return (state_email)

# Flow to test if the ovh API credentials are valid
@flow
def test_credentials():
    ovh_client = init_ovh()
    return ovh_client.get('/me')['firstname']

# Define the flow to launch the job
@flow
def job():
    ovh_client=init_ovh()
    res=launch_job(client=ovh_client,bucket_name="python-5742b54b-f5c1-4bbf-bca9-0ef4921f282a")
    return("Job Launched ! ")

# Run the flow for the data container and data
print("Welcome", test().get('/me')['firstname'],
      "Your data has been added in a S3 bucket")

# Run the flow for the notebook creation
print(f"Flow notebook {notebook()} !")

#Run the flow for the job creation
print(job())

# print("Welcome ",test_credentials())
