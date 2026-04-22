# Variable Group Setter & Generator for Azure DevOps

This project provides Python scripts to seamlessly sync JSON files with **Azure DevOps Variable Groups**, and vice-versa. 

> **Important Context:** These scripts are specially designed with **.NET `appsettings.json`** structures in mind. The tool automatically handles the complex flattening (e.g. `ConnectionStrings.DefaultDb`) and unflattening (including translating numeric indices like `Serilog.Enrich.0` into fully valid JSON arrays `[]`) natively expected by the ASP.NET Core Configuration Binder.

## Requirements

- Python 3.x
- An Azure DevOps **Personal Access Token (PAT)** with Variable Group read/write scopes.

## Authentication

Both scripts rely on the Azure DevOps REST API. You can provide your Personal Access Token in two ways:
1. Setting the `AZURE_DEVOPS_EXT_PAT` environment variable (Recommended for CI/CD).
2. Supplying the `--pat "your_token_here"` flag when running the scripts.

---

## 1. Upload variables (`setVariables.py`)

Takes a deeply nested JSON file (like a standard `appsettings.json`) and intelligently flattens it before pushing it to an Azure DevOps Variable Group.

### Usage

```bash
python3 setVariables.py <json_file> \
    --group-id <group_id> \
    --org <org_url> \
    --project <project_name> \
    [--action <create|update>] \
    [--pat <personal_access_token>]
```

### Arguments

- `json_file`: (Required) Path to the JSON file containing the variables to be set.
- `--group-id`: (Required) The ID of the Azure DevOps variable group.
- `--org`: (Required) The URL of your Azure DevOps organization (e.g., `https://dev.azure.com/my-org`).
- `--project`: (Required) The name of your Azure DevOps project.
- `--action`: (Optional) `create` to solely push *new* variables, or `update` to safely overwrite *existing* matching ones. Defaults to `update`.
- `--pat`: (Optional) Your Azure DevOps token. Falls back to `AZURE_DEVOPS_EXT_PAT`.

---

## 2. Generate appsettings.json (`generateAppSettings.py`)

Connects to an existing Azure DevOps Variable Group, extracts all keys, and decompresses dot notations (`.`) and double-underscores (`__`) to dynamically reconstruct a fully nested `.NET appsettings.json` file. It cleverly detects array patterns and converts secrets into `<SECRET_VALUE>` placeholders automatically.

### Usage

```bash
python3 generateAppSettings.py \
    --group-id <group_id> \
    --org <org_url> \
    --project <project_name> \
    [--out <output_path.json>] \
    [--pat <personal_access_token>]
```

### Arguments

- `--group-id`: (Required) The ID of the Azure DevOps variable group you want to export.
- `--org`: (Required) The URL of your Azure DevOps organization.
- `--project`: (Required) The name of your Azure DevOps project.
- `--out`: (Optional) Path to save the resulting JSON. Defaults to `appsettings.json` in the current directory.
- `--pat`: (Optional) Your Azure DevOps token. Falls back to `AZURE_DEVOPS_EXT_PAT`.

---

## 3. Mass Pipeline Trigger (`runAllPipelines.py`)

A dangerous yet powerful script that fetches and triggers all pipelines within an Azure DevOps project simultaneously. It incorporates safeguards like dry-runs and folder scoping to prevent agent pool exhaustion.

### Usage

```bash
python3 runAllPipelines.py \
    --org <org_url> \
    --project <project_name> \
    [--folder <\MyFolder>] \
    [--branch <main>] \
    [--dry-run] \
    [--pat <personal_access_token>]
```

### Arguments

- `--org`: (Required) The URL of your Azure DevOps organization.
- `--project`: (Required) The name of your Azure DevOps project.
- `--folder`: (Optional) Scope the launch to only pipelines located inside this ADO folder structure (e.g., `\Microservices`).
- `--branch`: (Optional) Specifically run pipelines against this branch. If omitted, triggers logic uses ADO's default branch per pipeline.
- `--dry-run`: (Optional) Simulates the execution. Prints which pipelines would be targeted without actually queueing them.
- `--pat`: (Optional) Your Azure DevOps token. Falls back to `AZURE_DEVOPS_EXT_PAT`.
