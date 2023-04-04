

# don't forget to : pip install ovh boto3 prefect (need a prefect.io free account)
# then : prefect auth login

import prefect
import ovh
import json
import boto3
import botocore

from pathlib import Path
from prefect import task, Flow, Parameter, case
from botocore.exceptions import ClientError
from datetime import timedelta


@task(log_stdout=True)
def init_ovh():
    # Login on OVH API
    # Visit https://api.ovh.com/createToken/?GET=/me to get your credentials
    ovh_client = ovh.Client(
        endpoint='ovh-eu',
        application_key='xxx',
        application_secret='xxx',
        consumer_key='xxx',
    )
    return ovh_client

@task(log_stdout=True)
def init_s3():
    # Log in OVHcloud Object Storage with S3 protocol
    # To get credentials, go to Control Panel / Public Cloud / (your project) / Users / (generate S3 credentials)
    # boto3 doc : https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html
    client = boto3.client(
        's3',
        aws_access_key_id="",
        aws_secret_access_key="",
        endpoint_url="https://s3.gra.cloud.ovh.net/",
        region_name="gra"
    )
    return client

@task(log_stdout=True, max_retries=3, retry_delay=timedelta(seconds=10))
def list_buckets(client):
    logger = prefect.context.get("logger")
    try:
        response = client.list_buckets()
        # Output the bucket names
        print('Existing buckets:')
        for bucket in response['Buckets']:
            print(f'  {bucket["Name"]}')
    except botocore.exceptions.ClientError as error:
        raise ValueError("Unable to List buckets")
    pass

@task(log_stdout=True, max_retries=3, retry_delay=timedelta(seconds=10))
def create_bucket(bucket, client):
    logger = prefect.context.get("logger")
    try:
        response = client.create_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            # We grab the message, request ID, and HTTP code to give to customer support
            print('Info : bucket already exist.')
        else:
            raise ValueError("Unable to create bucket")
    pass

@task(log_stdout=True, max_retries=3, retry_delay=timedelta(seconds=10))
def list_bucket_objects(bucket, client):
    logger = prefect.context.get("logger")
    try:
        response = client.list_objects_v2(Bucket=bucket, MaxKeys=10)
        print(response)
    except botocore.exceptions.ClientError as error:
        # Put your error handling logic here
        raise ValueError("Unable to list bucket objects.")
    pass

@task(log_stdout=True, max_retries=3, retry_delay=timedelta(seconds=10))
def check_local_data(directory):
    logger = prefect.context.get("logger")

    # Get a specific folder size and files listing
    root_directory = Path(directory)
    size = sum(f.stat().st_size for f in root_directory.glob(
        '**/*') if f.is_file())
    files = [x for x in root_directory.glob('**/*') if x.is_file()]

    print("Directory {} size is {} bytes".format(root_directory, size))

    # If i have at least 1MB of data then return files listing
    if size >= 1000:
        logger.info("Enough data to continue !")
        return files
    else:
        raise ValueError("Not enough data to perform a new upload")

@task(log_stdout=True, max_retries=3, retry_delay=timedelta(seconds=10))
def upload_data(files, bucket, client):
    logger = prefect.context.get("logger")
    # Upload a file to an S3 bucket
    # param file: File to upload
    # param bucket: Bucket to upload to
    # param object_name: S3 object name. If not specified then file_name is used
    # return: True if file was uploaded, else False

    # Upload files one by one
    for file in files:
        try:
            file = str(file)
            object_name = file
            print(file)
            response = client.upload_file(file, bucket, object_name)
        except ClientError as e:
            logging.error(e)
            return False
    pass

@task(log_stdout=True, max_retries=3, retry_delay=timedelta(seconds=10))
def new_job(framework, data_container, region_ovh, ovh):
    logger = prefect.context.get("logger")
    # Get a specific folder size and files listing
    result = ovh.post('/cloud/project/'+str(project_uuid)+'/ai/job', image=framework, region=region_ovh, resources={"gpu": 1}, volumes=[
                        {"region": "GRA", "container": "cobbai", "mountPath": "/workspace/container_0", "permission": "RW"}], name="New_job_via_prefect")

    # Pretty print if you want everything
    print(json.dumps(result, indent=4))
    # Return tje job id only
    return result['id']

@task(log_stdout=True)
def get_job_details(job_id, ovh):

    # Get job infiormation
    result = ovh.get('/cloud/project/' +
                        str(project_uuid)+'/ai/job/', job_id)

    # Pretty print if you want everything
    print(json.dumps(result, indent=4))

with Flow("AI Training") as flow:

    local_directory = Parameter(
        "Data directory", default="/Users/bverdebo/dataset/")
    region = Parameter("Region", default="GRA")
    project_uuid = Parameter(
        "Project uuid", default="10a1889e263d44048302dc8d8057203a")
    bucket_name = Parameter("Bucket name", default="cobbai")
    framework = Parameter(
        "framework", default="ovhcom/ai-training-one-for-all:v98")

    # Credentail initialization
    ovh_client = init_ovh()
    client = init_s3()

    # Data management
    granted = list_buckets(client)
    create_bucket = create_bucket(
        bucket_name, client, upstream_tasks=[granted])
    list_bucket_objects(bucket_name, client,
                        upstream_tasks=[create_bucket])
    data = check_local_data(
        local_directory, upstream_tasks=[create_bucket])
    upload = upload_data(data, bucket_name, client)

    # AI Training job creation
    job = new_job(framework, bucket_name, region,
                    ovh_client, upstream_tasks=[upload])
    get_job_details(job, ovh_client)

# Register the flow under the "tutorial" project
flow.register(project_name="OVH_cobbai")

flow.run()
