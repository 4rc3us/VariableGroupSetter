# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - Azure DevOps REST API & AppSettings Generator

### Added
- **`generateAppSettings.py` script:** A new powerful utility to extract variables from Azure DevOps and rebuild them into a deeply nested JSON.
  - Specially designed for **.NET `appsettings.json`**.
  - Supports unflattening dot notation (`.`) and double-underscore notation (`__`).
  - Implements intelligent array detection (e.g., automatically transforms `Serilog.Enrich.0` into a JSON array `[...]` instead of a dictionary).
  - Skips API secrets safely, inserting a `<SECRET_VALUE>` placeholder to avoid CI/CD breaks while still communicating structural requirements.
- Standard Native Authentication using the `AZURE_DEVOPS_EXT_PAT` environment variable or `--pat` flag.

### Changed
- **`setVariables.py` major refactor:** Replaced the legacy iterative `az cli subprocess` mechanism with a single batch `Azure DevOps REST API` payload. 
  - Reduced script execution time from minutes down to ~2 seconds.
  - Eliminated the dependency on installing or configuring `azure-cli`.
- Modified the `--action` flag behavior in `setVariables.py` to be extremely safe:
  - `--action create`: Will strictly add new keys from your JSON and ignore overriding existing variables.
  - `--action update`: Will strictly overwrite existing keys and ignore pushing entirely new keys.

## [1.0.0] - Initial Release

### Added
- Created `setVariables.py` to recursively traverse a JSON file and sequentially push keys to Azure DevOps using `az pipelines variable-group variable (create|update)` shell commands.
