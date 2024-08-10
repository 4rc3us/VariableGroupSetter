import json
import subprocess
import sys

def SetVariable(data, path=''):
    new_key = path
    if isinstance(data, dict):
        for k,v in data.items():
            new_key = f"{path}.{k}" if path else k
            SetVariable(v, new_key)
    elif isinstance(data, list):
        for i,v in enumerate(data):
            new_key = f"{path}.{i}" if path else f"{i}"
            SetVariable(v, new_key)
    else:
        cmd = f"az pipelines variable-group variable {isCreateOrUpdate} --detect false --group-id {group_id} --name {new_key} --value {json.dumps(data)} --org {org} --project \"{project}\""
        print(cmd)
        subprocess.run(cmd, shell=True)

json_path = sys.argv[1]
isCreateOrUpdate = sys.argv[2]
group_id = sys.argv[3]
org = sys.argv[4]
project = sys.argv[5]


with open(json_path) as f:
    data = json.load(f)

SetVariable(data)
