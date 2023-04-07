import requests
from dotenv import load_dotenv
import os

# Load environments variables
load_dotenv(".env")

with open("nlu.yml",'rb') as f:
    data=f.read()

token=os.getenv("OPEN_STACK_TOKEN")
headers={
    "X-Auth-Token": token,
    "Content-Type": "application/octet-stream"
}

response=requests.put(url=f'https://storage.gra.cloud.ovh.net/v1/AUTH_{os.getenv("PROJECT_ID")}/ai-notebook/data/nlu.yml',data=data,headers=headers)

print(response.text)

test=requests.get(url=f'https://storage.gra.cloud.ovh.net/v1/AUTH_{os.getenv("PROJECT_ID")}/ai-notebook/',headers={"X-Auth-Token": token})

print(test.text)