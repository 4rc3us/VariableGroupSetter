# Requirements

> This project was developed using Python 3.8.5. Although it should work on any Python 3.x version.
> azure cli is required to run the script. You can install it by following the instructions [here](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli#install).
> You will also need to have an Azure account. If you don't have one, you can create a free account [here](https://azure.microsoft.com/en-us/free/).

# How to run

1. Clone this repository's code
2. Open a terminal and navigate to the project's root folder
3. Run the following command to install the required dependencies:

```bash
python setVariables.py <json_path> <create|update> <group_id> <org> <project>
```

json_path = sys.argv[1]
isCreateOrUpdate = sys.argv[2]
group_id = sys.argv[3]
org = sys.argv[4]
project = sys.argv[5]
