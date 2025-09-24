# Requirements

> This project was developed using Python 3.8.5. Although it should work on any Python 3.x version.
> azure cli is required to run the script. You can install it by following the instructions [here](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli#install).
> You will also need to have an Azure account. If you don't have one, you can create a free account [here](https://azure.microsoft.com/en-us/free/).

# How to run

1. Clone this repository's code
2. Open a terminal and navigate to the project's root folder
3. Run the script using the following command structure:

```bash
python setVariables.py <json_file> --group-id <group_id> --org <org> --project <project> [--action <action>]
```

## Arguments

-   `json_file`: (Required) Path to the JSON file containing the variables to be set.
-   `--group-id`: (Required) The ID of the Azure DevOps variable group.
-   `--org`: (Required) The URL of your Azure DevOps organization (e.g., `https://dev.azure.com/your-org`).
-   `--project`: (Required) The name of your Azure DevOps project.
-   `--action`: (Optional) The action to perform. Can be `create` or `update`. Defaults to `update`.

## Example

```bash
python setVariables.py my_variables.json --group-id 12345 --org "https://dev.azure.com/my-awesome-org" --project "My-Awesome-Project" --action create
```
