# Import the libraries
from prefect import flow, task
import ovh
import json
import requests
from botocore.exceptions import ClientError
from prefect.blocks.notifications import SlackWebhook
from dotenv import load_dotenv
import os

# Load environments variables
load_dotenv(".env")


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




@task
def list_buckets(client):
    try:
        response=client.get(f'/cloud/project/{os.getenv("PROJECT_ID")}/storage')
        print (json.dumps(response, indent=4))
    except ClientError as error:
        raise ValueError("Unable to List buckets")
    pass


@task
def create_bucket(bucket, client):
    try:
        api_params={"archive":False,"containerName":"python-prefect","region":"GRA"}
        response= client.post(f'/cloud/project/{os.getenv("PROJECT_ID")}/storage',**api_params)
        print (json.dumps(response, indent=4))
    except ClientError as error:
        if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            # We grab the message, request ID, and HTTP code to give to customer support
            print('Info : bucket already exist.')
        else:
            raise ValueError("Unable to create bucket")
    return (response)


@task
def list_bucket_objects(bucket, client):
    try:
        result = client.get(f'/cloud/project/{os.getenv("PROJECT_ID")}/storage/63486c30614739754c5842795a575a6c5933517552314a42')
        print(json.dumps(result, indent=4))
    except ClientError as error:
        # Put your error handling logic here
        raise ValueError("Unable to list bucket objects.")
    pass


@task
def upload_data(file, bucket, client):
    # Upload a file to an S3 bucket
    # param file: File to upload
    # param bucket: Bucket to upload to
    # return: True if file was uploaded, else False
    try:
        token=os.getenv("OPEN_STACK_TOKEN")
        headers={
            "X-Auth-Token": token,
            "Content-Type": "text/csv"
        }
        response=requests.put(url=f"https://storage.gra.cloud.ovh.net/v1/AUTH_{os.getenv('PROJECT_ID')}/python-prefect/archive/data.csv",data=file,headers=headers)
        print(response)
    except ClientError as e:
        return False
    return True


@task
def launch_notebook(client, bucket_name):
    notebook_creation_params = {"env": {"editorId": "jupyterlab", "frameworkId": "conda", "frameworkVersion": "conda-py39-cuda11.7-v22-4"}, "envVars": None, "labels": None, "name": "prefect-2", "region": "GRA", "resources": {"cpu": 3, "flavor": "ai1-1-cpu"},
                                "sshPublicKeys": [], "unsecureHttp": False, "volumes": [{"cache": False, "dataStore": {"alias": "GRA", "container": "test-for-post", "prefix": None}, "mountPath": "/workspace/container_0", "permission": "RO"}]}
    result = client.post(f'/cloud/project/{os.getenv("PROJECT_ID")}/ai/notebook',
                         **notebook_creation_params)
    return result


@task
def get_state_notebook(result):
    status=result['status']['state']
    name=result['spec']['name']
    id=result['id']
    url=result['status']['url']
    slack_webhook_block = SlackWebhook.load("slack")
    slack_webhook_block.notify(f"Your notebook with the name {name} has been created ! \n")
    slack_webhook_block.notify(f"He is in state {status}")
    slack_webhook_block.notify(f"The id of the notebook is {id}")
    slack_webhook_block.notify(f"You can access it on this url : {url}")
    return "A message has been sent ! "



@flow
def test():
    ovh_client = init_ovh()
    list_buckets(ovh_client)
    bucket_name = "python-prefect"
    #create_bucket(bucket=bucket_name,client=ovh_client)
    list_bucket_objects(bucket=bucket_name, client=ovh_client)
    with open("archive/data.csv",'rb') as f:
        data=f.read()
    upload_data(file=data, bucket=bucket_name, client=ovh_client)
    return ovh_client

@flow
def notebook():
    ovh_client = init_ovh()
    res = launch_notebook(
        client=ovh_client, bucket_name="test-for-post")
    return(get_state_notebook(result=res))

@flow
def test_credentials():
    ovh_client = init_ovh()
    return ovh_client.get('/me')['firstname']

# Run the flow for the data container and data
print("Welcome", test().get('/me')['firstname'], "Your data has been added in a S3 bucket")


#print(notebook())

# print("Welcome ",test_credentials())
