# Import the libraries
# Import the prefect libraries in python
from prefect import flow, task
from prefect_email import EmailServerCredentials, email_send_message
import time

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