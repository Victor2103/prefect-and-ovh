import json

with open("test.json",'r') as f:
    object=json.load(f)
    status = object['status']['state']
    name = object['spec']['name']
    id = object['id']
    exitCode = object['status']['exitCode']
    print(status,name,id,exitCode)