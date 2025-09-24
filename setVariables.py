import json
import subprocess
import argparse
import sys

def set_variable(data, group_id, org, project, action, path=''):
    """
    Recursively traverses a dictionary or list and sets Azure DevOps variables.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{path}.{k}" if path else k
            set_variable(v, group_id, org, project, action, new_key)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_key = f"{path}.{i}" if path else f"{i}"
            set_variable(v, group_id, org, project, action, new_key)
    else:
        if not path:
            print("Error: The root of the JSON file must be an object or an array.", file=sys.stderr)
            sys.exit(1)
        # Using json.dumps to handle boolean and other types correctly for non-string values.
        if isinstance(data, str):
            value = data
        else:
            value = json.dumps(data)
        cmd = (
            f"az pipelines variable-group variable {action} "
            f"--detect false --group-id {group_id} --name \"{path}\" "
            f"--value '{value}' --org \"{org}\" --project \"{project}\""
        )
        print(f"Executing: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            if action == 'update' and 'does not exist' in e.stderr:
                print(f"Variable '{path}' does not exist, creating it.")
                create_cmd = (
                    f"az pipelines variable-group variable create "
                    f"--detect false --group-id {group_id} --name \"{path}\" "
                    f"--value '{value}' --org \"{org}\" --project \"{project}\""
                )
                print(f"Executing: {create_cmd}")
                try:
                    subprocess.run(create_cmd, shell=True, check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as create_e:
                    print(f"Error executing create command: {create_cmd}", file=sys.stderr)
                    print(f"Stderr: {create_e.stderr}", file=sys.stderr)
                    sys.exit(1)
            elif action == 'create' and 'already exists' in e.stderr:
                print(f"Variable '{path}' already exists, skipping.")
            else:
                print(f"Error executing command: {cmd}", file=sys.stderr)
                print(f"Stderr: {e.stderr}", file=sys.stderr)
                sys.exit(1)

def main():
    """
    Main function to parse arguments and start the variable setting process.
    """
    parser = argparse.ArgumentParser(description="Set variables in an Azure DevOps variable group from a JSON file.")
    parser.add_argument("json_file", help="Path to the JSON file containing variables.")
    parser.add_argument("--group-id", required=True, help="ID of the variable group.")
    parser.add_argument("--org", required=True, help="Azure DevOps organization URL (e.g., https://dev.azure.com/myorg).")
    parser.add_argument("--project", required=True, help="Name of the Azure DevOps project.")
    parser.add_argument(
        "--action",
        choices=["create", "update"],
        default="update",
        help="Action to perform: 'create' new variables or 'update' existing ones. Defaults to 'update'."
    )

    args = parser.parse_args()

    try:
        with open(args.json_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{args.json_file}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{args.json_file}'", file=sys.stderr)
        sys.exit(1)

    set_variable(data, args.group_id, args.org, args.project, args.action)

if __name__ == "__main__":
    main()
