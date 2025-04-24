# Vault Secret Rotator 🔐

A CLI tool for rotating secrets stored in HashiCorp Vault across multiple environments and applications.

## Features 🌟

- GitHub-based authentication for Vault access
- Support for multiple environments (prod, non-prod, testing)
- Rotate AWS credentials and other environment variables
- Handles dotenv format with export statements
- Path validation and detailed error reporting
- Interactive CLI with confirmation prompts

## Prerequisites 📋

- Python 3.x
- Access to HashiCorp Vault
- GitHub Personal Access Token with required scopes:
  - `read:org`
  - `repo` (if accessing private repos)

## Installation 🛠️

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration 📝

Create a `config.yaml` file with your Vault configuration:

```yaml
environments:
  prod:
    vault_url: "https://your-prod-vault-url"
    app1:
      paths:
        - "kv/data/path/to/your/secret"
  non_prod:
    vault_url: "https://your-non-prod-vault-url"
    app1:
      paths:
        - "kv/data/path/to/your/secret"

vault:
  mount_point: "kv"
```

## Usage 💻

Run the script:
```bash
python rotate_secrets.py
```

The script will:
1. Prompt for environment selection
2. Request GitHub token for authentication
3. Verify access to configured paths
4. Allow selection of application and secret type
5. Rotate the selected secrets

### Supported Secret Types 🔑

1. AWS Credentials:
   - AWS Access Key ID
   - AWS Secret Access Key

2. Environment Variables:
   - Any key-value pair in dotenv format
   - Maintains `export` prefix in the format

## Error Handling 🚨

The script provides detailed error messages for:
- Authentication failures
- Permission issues
- Invalid paths
- Secret rotation failures

## Security Notes 🛡️

- Sensitive inputs are masked during entry
- Confirmation required before making changes
- Token and secret values are masked in logs
- Uses Vault's KV v2 engine for versioning 