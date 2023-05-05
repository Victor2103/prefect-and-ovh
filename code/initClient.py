# Import the libraries
# Import the prefect libraries in python
from prefect import task, variables

# Import the ovh client and boto3 for s3 storage
import ovh
import boto3


import basePrefect


# First task to create an open stack token
@task(name="init-the-ovh-client",
      task_run_name=basePrefect.generate_task_name)
def init_ovh(username):
    # Visit https://api.ovh.com/createToken/?GET=/me to get your credentials
    ovh_client = ovh.Client(
        endpoint=appEndpoint,
        application_key=applicationKey,
        application_secret=applicationSecret,
        consumer_key=consumerKey,
    )
    return ovh_client

# Task to create a botoS3 client


@task(name="init-a-S3-user",
      task_run_name=basePrefect.generate_task_name)
def init_s3(username):
    # Log in OVHcloud Object Storage with S3 protocol
    # To get credentials, go to Control Panel / Public Cloud / (your project) / Users / (generate S3 credentials)
    # boto3 doc : https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html
    # For the credentials of boto3 use the S3 credentials created on the OVHcloud control pannel
    client = boto3.client(
        's3',
        aws_access_key_id=awsAccessKey,
        aws_secret_access_key=awsSecretKey,
        endpoint_url=endpointUrl,
        region_name=regionName
    )
    return client


# Get the variables from your environment in prefect cloud  :
appEndpoint = variables.get("app_endpoint", default="<your-app-endpoint>")
applicationKey = variables.get("app_key", default="<your-app-key>")
applicationSecret = variables.get(
    "app_secret", default="<your-application-secret")
consumerKey = variables.get("consumer_key", default="<your-consumer-key>")
awsAccessKey = variables.get("s3_key", default="<your-S3-access-key>")
awsSecretKey = variables.get("s3_secret", default="<your-S3-secret-key>")
endpointUrl = variables.get("s3_endpoint", "<your-S3-endpoint>")
regionName = variables.get("s3_region", default="<your-S3-region>")
