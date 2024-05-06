import json
import subprocess
import sys

def SetVariable(data, path=''):
    for k,v in data.items():
        new_key = f"{path}.{k}" if path else k
        if isinstance(v, dict):
            SetVariable(v, new_key)
        else:
            cmd = f"az pipelines variable-group variable create --detect false --group-id {group_id} --name {new_key} --value \"{v}\" --org https://dev.azure.com/CASProyectos/ --project \"OmniCanalidad y Cliente 360 - CRM\""
            print(cmd)
            subprocess.run(cmd, shell=True)

group_id = sys.argv[1]
json_path = sys.argv[2]

with open(json_path) as f:
    data = json.load(f)

SetVariable(data)
