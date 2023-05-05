# Import the libraries
# Import the prefect libraries in python
from prefect import task
import basePrefect

# Import error if the client
from botocore.exceptions import ClientError
# from prefect.blocks.notifications import SlackWebhook


# Task for listing all of your S3 buckets
@task(name="list-all-of-your-buckets",
      task_run_name=basePrefect.generate_task_name)
def list_buckets(client, username):
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
@task(name="create-a-S3-bucket",
      task_run_name=basePrefect.generate_task_name)
def create_bucket(bucket_name, client, region, username):
    try:
        location = {'LocationConstraint': region}
        response = client.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration=location)
    except ClientError as error:
        return (False)
    return (True)


# Task to list all of the objects inside a bucket
@task(name="list_object-in-yourS3-bucket",
      task_run_name=basePrefect.generate_task_name)
def list_bucket_objects(bucket, client, username):
    try:
        response = client.list_objects_v2(Bucket=bucket, MaxKeys=10)
        print(response)
    except ClientError as error:
        # Put your error handling logic here
        raise ValueError("Unable to list bucket objects.")
    pass


# Task to upload some files in a S3 bucket
@task(name="upload-files-in-a-S3-bucket",
      task_run_name=basePrefect.generate_task_name)
def upload_data(files, bucket, client, username):
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
