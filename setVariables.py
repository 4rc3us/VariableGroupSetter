import json
import argparse
import sys
import os
import base64
import urllib.request
import urllib.error
import urllib.parse

def flatten_json(data, path=''):
    """
    Recursively flattens a dictionary or list into a flat dictionary with dot notation keys.
    """
    flat_dict = {}
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{path}.{k}" if path else k
            flat_dict.update(flatten_json(v, new_key))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_key = f"{path}.{i}" if path else f"{i}"
            flat_dict.update(flatten_json(v, new_key))
    else:
        # For leaf nodes, assign them as strings compatible with Azure DevOps variables
        if isinstance(data, str):
            value = data
        else:
            value = json.dumps(data)
        flat_dict[path] = value
    return flat_dict

def get_variable_group(org, project, group_id, headers):
    """
    Fetches the entire variable group payload from Azure DevOps REST API.
    """
    org = org.rstrip("/")
    project = urllib.parse.quote(project)
    url = f"{org}/{project}/_apis/distributedtask/variablegroups/{group_id}?api-version=6.0-preview.2"
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error fetching variable group: {e.code} - {e.reason}", file=sys.stderr)
        try:
            print(e.read().decode(), file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)

def update_variable_group(org, project, group_id, data, headers):
    """
    Updates the variable group via Azure DevOps REST API.
    """
    org = org.rstrip("/")
    project = urllib.parse.quote(project)
    url = f"{org}/{project}/_apis/distributedtask/variablegroups/{group_id}?api-version=6.0-preview.2"
    
    json_data = json.dumps(data).encode("utf-8")
    
    put_headers = headers.copy()
    put_headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=json_data, headers=put_headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error updating variable group: {e.code} - {e.reason}", file=sys.stderr)
        try:
            print(e.read().decode(), file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Set variables in an Azure DevOps variable group from a JSON file using the REST API.")
    parser.add_argument("json_file", help="Path to the JSON file containing variables.")
    parser.add_argument("--group-id", required=True, help="ID of the variable group.")
    parser.add_argument("--org", required=True, help="Azure DevOps organization URL (e.g., https://dev.azure.com/myorg).")
    parser.add_argument("--project", required=True, help="Name of the Azure DevOps project.")
    parser.add_argument(
        "--action",
        choices=["create", "update"],
        default="update",
        help="Action to perform: 'create' only new variables, or 'update' only existing ones. Defaults to 'update'."
    )
    parser.add_argument(
        "--pat", 
        help="Azure DevOps Personal Access Token. If not provided, falls back to AZURE_DEVOPS_EXT_PAT environment variable."
    )

    args = parser.parse_args()

    # Get PAT from arguments or Environment
    pat = args.pat or os.environ.get("AZURE_DEVOPS_EXT_PAT")
    if not pat:
        print("Error: Personal Access Token (PAT) is required. Provide it via the --pat argument or the AZURE_DEVOPS_EXT_PAT environment variable.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.json_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{args.json_file}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{args.json_file}'", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, (dict, list)):
        print("Error: The root of the JSON file must be an object or an array.", file=sys.stderr)
        sys.exit(1)

    # 1. Flatten the input JSON into a single dictionary mapping dot-paths to string values
    flat_vars = flatten_json(data)
    
    # 2. Build authentication headers with Base64 encoding
    encoded_pat = base64.b64encode(f":{pat}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded_pat}",
        "Accept": "application/json"
    }

    print(f"Fetching current variable group [{args.group_id}] state...")
    # 3. Retrieve the existing variable group from ADO
    vg_data = get_variable_group(args.org, args.project, args.group_id, headers)
    
    variables = vg_data.get("variables", {})
    changes_made = False

    print(f"Processing variables with action: {args.action}")
    
    # 4. Integrate flat JSON into the variable group according to specified 'action'
    if args.action == "update":
        for key, value in flat_vars.items():
            if key in variables:
                # Retain secret states if necessary, but we are overwriting value here
                variables[key]["value"] = str(value)
                print(f" -> Will update '{key}'.")
                changes_made = True
            else:
                print(f" -> Skipping '{key}' (does not exist in ADO variable group).")
    
    elif args.action == "create":
        for key, value in flat_vars.items():
            if key in variables:
                print(f" -> Skipping '{key}' (already exists in ADO variable group).")
            else:
                variables[key] = {"value": str(value)}
                print(f" -> Will create '{key}'.")
                changes_made = True

    if not changes_made:
        print("No changes required. Exiting without updating the variable group.")
        sys.exit(0)

    # Reattach the updated variables dict back to the payload root
    vg_data["variables"] = variables

    # 5. Push the updated group payload back to ADO
    print(f"\nSending PUT request to update the variable group...")
    update_variable_group(args.org, args.project, args.group_id, vg_data, headers)
    print("Variable group successfully updated.")

if __name__ == "__main__":
    main()
