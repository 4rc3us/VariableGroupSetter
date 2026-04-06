import json
import argparse
import sys
import os
import base64
import urllib.request
import urllib.error
import urllib.parse

def object_to_array(data):
    """
    Recursively converts dictionaries with exclusively numeric keys (e.g. "0", "1")
    into actual JSON arrays.
    """
    if not isinstance(data, dict):
        return data
    
    # Process children first
    for k, v in data.items():
        data[k] = object_to_array(v)
        
    if not data:
        return data
        
    # Check if all keys represent integers
    if all(k.isdigit() for k in data.keys()):
        int_keys = [int(k) for k in data.keys()]
        # Small sanity check: if the lowest index is 0 and max index isn't crazy large
        if min(int_keys) == 0 and max(int_keys) < 1000:
            result_array = [None] * (max(int_keys) + 1)
            for k, v in data.items():
                result_array[int(k)] = v
            return result_array

    return data

def unflatten_json(flat_dict):
    """
    Converts a flat dictionary with dot (.) or double underscore (__) notation 
    into a nested dictionary structure, and automatically formats numeric keys into arrays.
    """
    result = {}
    for key, value in flat_dict.items():
        # Normalize double underscores to dots for consistent splitting
        normalized_key = key.replace('__', '.')
        parts = normalized_key.split('.')
        
        current = result
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Try to load string booleans/numbers as native JSON types if possible
                try:
                    parsed_value = json.loads(value) if isinstance(value, str) else value
                except (ValueError, TypeError):
                    parsed_value = value
                
                # If there's an existing dict at this level due to mixed naming, handle collision
                if part in current and isinstance(current[part], dict):
                    current[part]["_value"] = parsed_value
                else:
                    current[part] = parsed_value
            else:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    # Value collision, upgrade simple value to dict structure
                    current[part] = {"_value": current[part]}
                current = current[part]
                
    return object_to_array(result)

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

def main():
    parser = argparse.ArgumentParser(description="Generate appsettings.json from an Azure DevOps variable group.")
    parser.add_argument("--group-id", required=True, help="ID of the variable group.")
    parser.add_argument("--org", required=True, help="Azure DevOps organization URL (e.g., https://dev.azure.com/myorg).")
    parser.add_argument("--project", required=True, help="Name of the Azure DevOps project.")
    parser.add_argument(
        "--out", 
        default="appsettings.json", 
        help="Path to the output JSON file. Defaults to 'appsettings.json' in the current directory."
    )
    parser.add_argument(
        "--pat", 
        help="Azure DevOps Personal Access Token. If not provided, falls back to AZURE_DEVOPS_EXT_PAT environment variable."
    )

    args = parser.parse_args()

    pat = args.pat or os.environ.get("AZURE_DEVOPS_EXT_PAT")
    if not pat:
        print("Error: Personal Access Token (PAT) is required. Provide it via the --pat argument or the AZURE_DEVOPS_EXT_PAT environment variable.", file=sys.stderr)
        sys.exit(1)

    # Build authentication headers with Base64 encoding
    encoded_pat = base64.b64encode(f":{pat}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded_pat}",
        "Accept": "application/json"
    }

    print(f"Fetching variable group [{args.group_id}] state from Azure DevOps...")
    vg_data = get_variable_group(args.org, args.project, args.group_id, headers)
    
    variables = vg_data.get("variables", {})
    if not variables:
        print("Warning: The variable group is empty or no variables were returned.")
    
    # Process variables
    flat_vars = {}
    secret_count = 0

    for key, var_obj in variables.items():
        is_secret = var_obj.get("isSecret", False)
        
        if is_secret:
            # The REST API does not return the 'value' property for secret variables without specific permissions/pipeline runs
            flat_vars[key] = "<SECRET_VALUE>"
            secret_count += 1
        else:
            # We enforce standard value mapping
            flat_vars[key] = var_obj.get("value", "")

    print(f"Discovered {len(variables)} variables. ({secret_count} were secrets).")

    # Unflatten into hierarchical appsettings dict
    appsettings_data = unflatten_json(flat_vars)

    # Save to file
    try:
        with open(args.out, "w") as f:
            json.dump(appsettings_data, f, indent=4)
        print(f"Successfully generated '{args.out}'.")
    except IOError as e:
        print(f"Error saving file '{args.out}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
