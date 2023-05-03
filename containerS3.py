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
def create_bucket(bucket_name, client, region):
    try:
        print("ok")
        location = {'LocationConstraint': region}
        print("ok")
        response = client.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration=location)
    except ClientError as error:
        if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
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