# Import the libraries
# Import the prefect libraries in python
from prefect import flow, task, variables
from prefect_email import EmailServerCredentials, email_send_message
import time
import initClient
import containerS3
import basePrefect


# Define the task to launch a job


@task(name="launch-an-training-job",
      task_run_name=basePrefect.generate_task_name)
def launch_job(client, bucket_name, region_job, alias_s3, docker_image, name_job, cpu, username):
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
        f"/cloud/project/{projectUuid}/ai/job", **job_creation_params)
    return (result)


@task(name="wait-for-the-state-finish-of-the-job",
      task_run_name=basePrefect.generate_task_name)
def wait_state(client, id, username):
    wait = True
    while wait:
        res = client.get(
            f"/cloud/project/{projectUuid}/ai/job/{id}")
        status = res['status']['state']
        if (status == "DONE"):
            name = res['spec']['name']
            exitCode = res['status']['exitCode']
            wait = False
        else:
            time.sleep(60)
    return (name, exitCode, status, id)


# Flow to create an S3 bucket and upload files in it
@flow(name="create-a-S3-container-and-upload-your-data",
      flow_run_name=basePrefect.generate_flow_name)
def create_and_upload_in_S3(username):
    # Run the first task
    client = initClient.init_s3(username=username)
    bucket_name = "python-eae22d77-77e6-4db0-a4d4-f80831b0fa3a"
    # Run the second task
    containerS3.create_bucket(bucket_name=bucket_name,
                              client=client, region="gra",
                              username=username)
    files = ["my-dataset.zip", "train-first-model.py", "requirements.txt"]
    # Run the third task
    res = containerS3.upload_data(
        files=files, bucket=bucket_name, client=client, username=username)
    if res == True:
        # Run the fourth task
        containerS3.list_bucket_objects(
            bucket=bucket_name, client=client, username=username)
    else:
        raise Exception("Sorry, we can't upload your data")
    return client

# Define the flow to launch the job


@flow(name="launch-your-ai-training-job-link-to-an-S3-bucket",
      flow_run_name=basePrefect.generate_flow_name)
def job(username):
    ovh_client = initClient.init_ovh(username=username)
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
                     cpu=cpu,
                     username=username)
    return (wait_state(client=ovh_client, id=res["id"], username=username))

# Function to send an email to the user to be notified when the job is done.
# You need to create a block with your email credentials on prefect cloud.
# The name of my block here is email-block


@flow(name="send-email-with-details-of-the-job",
      flow_run_name=basePrefect.generate_flow_name)
def email(state_job, exit_code, id_job, name_job, username):
    email_credentials_block = EmailServerCredentials.load("email-block")
    line_1 = f"Your job with the name {name_job} is finished ! <br>"
    line_2 = f"He is in state {state_job}. <br>"
    line_3 = f"The id of the job is {id_job}. <br>"
    line_4 = f"He has return exit code {exit_code} <br>."
    message = line_1+line_2+line_3+line_4
    subject = email_send_message.with_options(name="send-an-email",
                                              task_run_name=f"send-an-email-by-{username}-to-notified-job_is_finished").submit(
        email_server_credentials=email_credentials_block,
        subject="Your job via prefect",
        msg=message,
        email_to="victor.vitcheff@ovhcloud.com",
    )
    return (subject)


# Get the username and create a prefect variables to send to the task
myUsername = variables.get('username', default="marvin")

# Get the project_uiid variable via the prefect cloud UI
projectUuid = variables.get(
    "project_uiid", default="<your-project-uuid>")

# Run the flow for the data container and data
print("Welcome", create_and_upload_in_S3(username=myUsername),
      "Your data has been added in a S3 bucket")

# Run the flow for the job creation
name, exitCode, status, id = job(username=myUsername)

# Send an email when it is over
email(state_job=status,
      exit_code=exitCode,
      id_job=id,
      name_job=name,
      username=myUsername)
