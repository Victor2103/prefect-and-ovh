---
title: Tutorial - AI Training - End-to-End pipeline with data ingestion and model training
slug: prefect/end-to-end-pipeline
excerpt: Create your first AI pipeline in a public Cloud by launching an AI Training job link to a S3 bucket with Prefect
section: Prefect
order: 03
updated: 2024-04-06
---

**Last updated 06th April 2024**
 
## Objective
 
The purpose of this tutorial is to create a pipeline from the ingestion of data in a S3 object storage to the email send when your AI Training job is done/failed/interrupted. We will launch a flow in Prefect which will simulate an AI Training job in a Public cloud project. To make the connection between Prefect and our public cloud project, we will use the OVHcloud's API. The main goal is to show that we can launch AI training jobs without having to monitor their state over time. Prefect can do this for us. 

To sucess this objective, we will first of all some data on a S3 object storage container. The data will be use to train the model, we will link it to our AI Training job. The model will be a **Torch** model. If you want to have some details about this model, fill free to look at this [tutorial](https://docs.ovh.com/gb/en/publiccloud/ai/training/tuto-train-first-ml-model/). All of this will be ensure with the Prefect tool configured in your python environment. The creation of the S3 object storage and the data upload will be done in a first Prefect flow. The second flow will be the launch of the job on AI Training. The last flow will be the email to send to the user. Here is the schema to understand what we will ensure in this tutorial :

![schema_flow](images/flows_email_job.png){.thumbnail}

## Requirements

- An environment to code with Prefect and OVHcloud's API. See this [tutorial](Getting-started)
- A Prefect cloud profile and a Prefect workspace open. See this [tutorial](Getting-started)
- Access to the [OVHcloud Control Panel](https://www.ovh.com/auth/?action=gotomanager&from=https://www.ovh.co.uk/&ovhSubsidiary=GB)
- A [Public Cloud project](https://www.ovhcloud.com/en-gb/public-cloud/)
- A S3 data store configured (you can do this easily with the cli : `ovhai data store ls`. XXXX I don't know where is the tutorial for this and if there is a tutorial. If no tutorial, I must explain.  

## Instructions


### Get Credentials for S3 protocol

To create a S3 object storage, we must provide With the [SDK OVHcloud](https://github.com/ovh/python-ovh), we can easily communicate with the OVHcloud's API. To interact with S3 object container, we must use a S3 protocol. OVHcloud don't provide this protocol yet but The [boto3 library](https://github.com/boto/boto3) provides it. The boto3 SDK is the Amazon Web Services (AWS) Software Development Kit (SDK) for Python, which allows Python developers to write software that makes use of services like S3 containers. It provides a low-level interface to many of the services, as well as higher-level abstractions that make it easier to work with those services. 

We need some credentials to use this protocol. You can get your credentials as S3 users. You can create them on the OVHcloud control panel, in your public cloud project in the object storage tab. If you want to know more about this credentials, it's [here](https://docs.ovh.com/gb/en/storage/object-storage/s3/identity-and-access-management/). Keep the access key and the secret key, we will need them later. 

Ok, now let's synchronize our S3 credentials with the boto3 client. To do this, we have to create a folder and two files in it. To configurate the boto3 client, I suggest you to follow this part of the [tutorial](https://docs.ovh.com/gb/en/storage/object-storage/pcs/getting-started-with-the-swift-s3-api/#configure-aws-client). Once the two files are created and you fill them with your credentials, we can start coding and create our S3 object storage with a Prefect flow !

### Create environments variables inside our prefect cloud workspace. 

Before starting our first task, we must store environments variables. Instead of storing them in a `.env` file, we can do this directly on the prefect cloud UI. In prefect, variables enable you to store and reuse non-sensitive bits of data, such as configuration information. Variables are named, mutable string values, much like environment variables. Variables are scoped to a Prefect Server instance or a single workspace in Prefect Cloud. To find more information, you can go directly on their [website](https://docs.prefect.io/latest/concepts/variables/). 

For this pipeline, we will create 9 variables. Most of them are your S3 access key or your credentials for the OVHcloud API. Here is the resume of the 9 varibles to create on the UI :
- app_endpoint = the endpoint of the OVHcloud API. It can be the europe endpoint for example. 
- app_key = your application key to access the OVHcloud API's. 
- app_secret = your application secret key to access the OVHcloud API's. 
- consumer_key = your consumer key to access the OVHcloud API's.
- s3_key = your S3 key to configure the botoS3 client
- s3_secret = your S3 secret key to configure the botoS3 client
- s3_endpoint = your S3 endpoint
- s3_region = the name of the region where your s3 bucket will be store
- project_uuid = your public cloud project id, you can found it on the url. 

Once your variable are created in the UI, you have to call them on your workspace in python. This will be ensure by a simple function directly provide by the SDK prefect for python. Let's take a look at this code :

```python
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
projectUuid = variables.get(
    "project_uiid", default="<your-project-uuid>")
```

By default, your variables are not shown to a random user. We can configure them directly on the prefect cloud UI. Ok now, let's create our first flow by creating and upload some data in a S3 bucket. But just before this, to understand the concept of prefect, we must name our flows and our tasks. Of course, you can putting all of your code in a single flow function with a no name flow — Prefect will happily run it! But organizing your workflow code into smaller flow and task units lets you take advantage of Prefect features like retries, more granular visibility into runtime state, the ability to determine final state regardless of individual task state, and more. To easily name your flows and tasks, we can create two functions who will take as parameters your username (choose whatever you want, for my case we will use OVHcloud !). This username is defined as a prefect variable (directly via the UI). 

### Create functions to generate flow and task name

As say previously, here are the two functions to generate our tasks and flows name ! More information about tasks and flows can be found [here](https://docs.prefect.io/latest/concepts/flows/). 

```python
def generate_task_name():
    task_name = task_run.task_name

    parameters = task_run.parameters
    name = parameters["username"]
    date = datetime.datetime.utcnow()

    return f"{task_name}-by-{name}-on-{date}"


def generate_flow_name():
    flow_name = flow_run.flow_name

    parameters = flow_run.parameters
    name = parameters["username"]
    date = datetime.datetime.utcnow()

    return f"{flow_name}-by-{name}-on-{date}"
```

Now, let's create our first flow, we are ready to begin. 

 
### Create a flow for our S3 object storage

In this part, we will create the first flow for our S3 object storage. First of all, we will create a task (@first-task on the schema) to initialize our boto3 client. Let's do this in our python environment !

```python
@task(name="init-a-S3-user",
      task_run_name=generate_task_name)
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
```

> [!primary]
>
> The **endpoint_url** should look something like this : https://s3.gra.io.cloud.ovh.net/. In this case, your region name is gra. The access and secret key is your credentials, you create them in the last step.  
>
 
Now, let's create the second task. For this task, we will need a name for our bucket. To name an S3 object storage, you need to provide a unique object key which serves as the identifier for the object. The object key consists of the bucket name and a unique identifier, separated by a tiret (-). To get this unique identifier, you can use a timestamp or [UIID generator](https://www.uuidgenerator.net/). Here is the python code to create our second task. 

```python
@task
@task(name="create-a-S3-bucket",
      task_run_name=generate_task_name)
def create_bucket(bucket_name, client, region, username):
    try:
        location = {'LocationConstraint': region}
        response = client.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration=location)
    except ClientError as error:
        return (False)
    return (True)
```

> [!warning]
> 
> In this task, we handle the error. If there is a Client Error because the credentials are false, the task will return False. After we will be able to do something with the result of the task, for example we can raise an error if the task return False because it didn't work successfully. 
>

Now, let's upload our data is the container ! We will upload in the container some code to create the model and extract our data, a requirements file and a .zip file with all the data to train. The python file and the requirements file can be downloaded on this [git repo](https://github.com/ovh/ai-training-examples/tree/main/jobs/getting-started/train-first-model). The dataset can be found on Kaagle [here](https://www.kaggle.com/datasets/zalando-research/fashionmnist). Let's create this task !

```python
@task(name="upload-files-in-a-S3-bucket",
      task_run_name=generate_task_name)
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
```

Now, let's define our last task to list all of the objects from our bucket. In the schema, this is our fourth task for the first flow ! 

```python
@task(name="list_object-in-yourS3-bucket",
      task_run_name=generate_task_name)
def list_bucket_objects(bucket, client, username):
    try:
        response = client.list_objects_v2(Bucket=bucket, MaxKeys=10)
        print(response)
    except ClientError as error:
        # Put your error handling logic here
        raise ValueError("Unable to list bucket objects.")
    pass
```

> [!primary]
>
> In this function, we don't return a parameter because we already print the objects. All tasks have to return something but you can pass the return with the key word pass. 
>

Our 4 tasks for the first flow has been created. Now, we have to define our variables in the flow and launch the 4 tasks. Let's do this !

```python
# Flow to create an S3 bucket and upload files in it
@flow(name="create-a-S3-container-and-upload-your-data",
      flow_run_name=generate_flow_name)
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
```

> [!warning]
> 
> Don't forget to download the data on your environment. If you don't do it, it can't be upload on the S3 object storage. 
>

### Create a flow for our job 

Let's create the last flow for our job. In this flow, we will need a python client who can connect to the OVHcloud's API. This is our first task. If you follow the [getting started tutorial](link), you should be able to have this task already. So let's go on and create the task to run our first job in our Public Cloud project !

The second task will use the SDK ovh for python. This library provides a post method on the url we want from the API. According to the API, we will use this [url](https://api.ovh.com/console/#/cloud/project/%7BserviceName%7D/ai/job~POST) :

> [!api]
>
> @api {POST}  /cloud/project/{serviceName}/ai/job
>

To launch a job, we must define some parameters. We can't launch a job with no name and no image. With the sdk ovh, parameters are really easy to provide. The function **client.post("url",\*\*job_params)** has two parameters. The first one is the url of the post request. The second one is a json object with all of the parameters of your job. If you not sure about how the body of the request is, you can open a console and launch your job with the OVHcloud control pannel. In this case, you will be able to see all of the json file. Here is a picture to show you how to get the raw data to send when you launch a job. 

![button_job](images/button_job.png){.thumbnail}

To resume, just before clicking on create, open a console, click and retrieve the request you send. This will give you a model of the **job_params** you must provide. 
Now, we have our object storage with the data upload, we have the parameters of the job to send to the OVHcloud client in python, let's create the task who will launch the job. Here is the python code :

```python
# Define the task to launch a job
@task(name="launch-an-training-job",
      task_run_name=generate_task_name)
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
``` 

Lots of parameters are present in this function ! There are all the parameters we can provide when you launch a job (number of cpu, name of your dockerfile, command to launch in the dockerfile, etc..). You can modify this request if you want. Now, let's define the last task of the schema, the third task ! 
But how can I know my job is done or failed ? I must get his state. Thanks to the API, when you do the post request of your job, you retrieve all of the infos of your notebook. In our example, we will just get the id and with this id we will do a get request every one minute to get the state of the notebook. Here is the reference to the API :

> [!api]
>
> @api {GET}  /cloud/project/{serviceName}/ai/job/{jobId}
>

Here is the task who handled the check of the end of the job. 

```python
@task(name="wait-for-the-state-finish-of-the-job",
      task_run_name=generate_task_name)
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
```

Ok now, let's start the last flow and send an email to notify that our job is over. We have to do a new flow because the sending an email is task who already exist and we can't create a task inside a task. So we create a flow with the parameters we want to send in the email and in this flow we send the task (email). Before create the task, don't forget to create an `Email Server Credentials` block directly on the prefect cloud UI. More information for this can be found [here](https://prefecthq.github.io/prefect-email/). You can also do this with python code. This configuration of the email allows prefect to send email with the credentials of one of your address mail. Now, let's define the last flow ! 

```python
@flow(name="send-email-with-details-of-the-job",
      flow_run_name=generate_flow_name)
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
```

We define all of our flows. Now, let's run this ! 

### Run the three flows

Before running the flow, make sure you install prefect-email. You should already have done that if you followed the tutorial to create the `Email Server Credentials` block. The last thing to do is launch the function which prefect will understand them as flow or task. Let's do this !

```python
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
```

Open a terminal, launch the command `python3 <name-of-your-file.py` and wait until it's done. We should have receive an email like this : 

![email_example](images/email_example.png){.thumbnail}

Now, let's see on the prefect cloud UI all the tools provided to see your flows ! For example, the "Flow Runs" tab in the Prefect Cloud UI displays information about the executions of your Prefect flows. Ypu can found the name of the flows, the state of the flow, the tasks run inside the flow and much more information about your running or runned flows. Overall, the Flow Runs tab provides a detailed overview of the execution history of your Prefect flows, allowing you to monitor performance, troubleshoot issues, and make improvements to your workflows. Here is an example : 

![interface_flows](images/flow_run_example.png){.thumbnail}

I choose to display the launch of the notebook, the second flow of this pipeline. We can see our three task display on the graph. We also see the order to execute them. Below the graph, you can found some tab to see the details of your tasks or the results of each task.

You also have the possibility to see the steps of your flows directly in the console but it is less precise than directly on the prefect cloud UI.   

## Go further
 
If you want to learn more about prefect, it's here : [Documentation Prefect](https://docs.prefect.io/latest/)

To see all the reference of the OVHcloud API, let's go here : [OVHcloud API](https://api.ovh.com/console/)

If you want to learn about AI Training jobs you can check tutorials on the OVHcloud documentation : [AI Training - Tutorials](https://help.ovhcloud.com/csm/en-gb-documentation-public-cloud-ai-and-machine-learning-ai-training-tutorials?id=kb_browse_cat&kb_id=574a8325551974502d4c6e78b7421938&kb_category=aa3a6120b4d681902d4cf1f95804f442)

## Feedback

Please send us your questions, feedback and suggestions to improve the service:

- On the OVHcloud [Discord server](https://discord.gg/ovhcloud)