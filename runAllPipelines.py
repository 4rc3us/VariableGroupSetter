import json
import argparse
import sys
import os
import base64
import urllib.request
import urllib.error
import urllib.parse
import time

def get_pipelines(org, project, headers):
    """
    Fetches all pipelines from the Azure DevOps project.
    """
    org = org.rstrip("/")
    project = urllib.parse.quote(project)
    url = f"{org}/{project}/_apis/pipelines?api-version=7.1"
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("value", [])
    except urllib.error.HTTPError as e:
        print(f"Error fetching pipelines: {e.code} - {e.reason}", file=sys.stderr)
        try:
            print(e.read().decode(), file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)

def trigger_pipeline(org, project, pipeline_id, pipeline_name, headers, branch=None):
    """
    Triggers a run for a specific pipeline ID.
    """
    org = org.rstrip("/")
    project = urllib.parse.quote(project)
    url = f"{org}/{project}/_apis/pipelines/{pipeline_id}/runs?api-version=7.1"
    
    # Body payload
    payload = {}
    if branch:
        payload = {
            "resources": {
                "repositories": {
                    "self": {
                        "refName": f"refs/heads/{branch}" if not branch.startswith("refs/") else branch
                    }
                }
            }
        }
        
    json_data = json.dumps(payload).encode("utf-8")
    
    post_headers = headers.copy()
    post_headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=json_data, headers=post_headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            run_url = result.get('_links', {}).get('web', {}).get('href', 'Unknown URL')
            print(f"[SUCCESS] Triggered '{pipeline_name}' (ID: {pipeline_id}) -> {run_url}")
            return True
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Failed to trigger '{pipeline_name}' (ID: {pipeline_id}): {e.code} - {e.reason}", file=sys.stderr)
        try:
            print(e.read().decode(), file=sys.stderr)
        except Exception:
            pass
        return False

def main():
    parser = argparse.ArgumentParser(description="Trigger all Azure DevOps pipelines in a project automatically.")
    parser.add_argument("--org", required=True, help="Azure DevOps organization URL (e.g., https://dev.azure.com/myorg).")
    parser.add_argument("--project", required=True, help="Name of the Azure DevOps project.")
    
    parser.add_argument(
        "--folder", 
        help="Optional. Only trigger pipelines that reside within this specific folder path (e.g., '\\MyServices')."
    )
    parser.add_argument(
        "--branch", 
        help="Optional. The branch to run the pipelines from (e.g., 'main'). If omitted, runs from the pipeline's default branch."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the execution. Prints which pipelines would be triggered without actually launching them."
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

    encoded_pat = base64.b64encode(f":{pat}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded_pat}",
        "Accept": "application/json"
    }

    print(f"Fetching pipelines from {args.project}...")
    pipelines = get_pipelines(args.org, args.project, headers)
    
    if not pipelines:
        print("No pipelines were found in this project.")
        sys.exit(0)
        
    print(f"Found {len(pipelines)} total pipelines.")
    
    # Filter by folder if specified
    pipelines_to_run = []
    if args.folder:
        # Normalize folder slashes for comparison
        target_folder = args.folder.replace('/', '\\')
        if not target_folder.startswith('\\'):
            target_folder = '\\' + target_folder
            
        for p in pipelines:
            p_folder = p.get('folder', '\\').replace('/', '\\')
            if p_folder == target_folder or p_folder.startswith(target_folder + '\\'):
                pipelines_to_run.append(p)
                
        print(f"Filtered down to {len(pipelines_to_run)} pipelines located in or under '{args.folder}'.")
    else:
        pipelines_to_run = pipelines

    if not pipelines_to_run:
        print("No pipelines matched your criteria. Exiting.")
        sys.exit(0)

    if args.dry_run:
        print("\n--- DRY RUN MODE ENABLED ---")
        print("The following pipelines would be triggered:")
        for idx, p in enumerate(pipelines_to_run, 1):
            name = p.get('name', 'Unknown')
            folder = p.get('folder', '\\')
            pid = p.get('id')
            print(f"  {idx}. [ID: {pid}] {folder}\\{name}")
        print("\nNo pipelines were actually triggered.")
        sys.exit(0)

    print("\nStarting execution...")
    success_count = 0
    failure_count = 0
    
    for p in pipelines_to_run:
        pid = p.get('id')
        name = p.get('name', 'Unknown')
        
        if trigger_pipeline(args.org, args.project, pid, name, headers, args.branch):
            success_count += 1
        else:
            failure_count += 1
            
        # Sleep briefly to avoid abusing the REST API or locking resources instantly
        time.sleep(0.5)

    print("\n--- EXECUTION SUMMARY ---")
    print(f"Successfully triggered: {success_count}")
    print(f"Failed to trigger: {failure_count}")

if __name__ == "__main__":
    main()
