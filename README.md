# Vault Secret Rotator 🔐

A CLI tool for rotating secrets stored in HashiCorp Vault across multiple environments and applications.

## Features 🌟

- GitHub-based authentication for Vault access
- Support for multiple environments (prod, non-prod, testing)
- Rotate AWS credentials and other environment variables
- Multiple secret format support:
  - `dotenv_export`: Environment variables with export statements
  - `dotenv_plain`: Simple key=value format
  - `json`: JSON format for structured data
- Custom AWS key name mapping per path and format
- Path validation and detailed error reporting
- Interactive CLI with confirmation prompts
- Smart secret key preservation across rotations

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
        - path: "kv/data/path/to/your/secret"
          format: "json"  # Specify format: json, dotenv_plain, or dotenv_export
          key: "secrets"  # Key under which secrets are stored
          aws_keys:  # Optional: Custom AWS key names for this path
            access_key: "S3_ACCESS_KEY"
            secret_key: "S3_SECRET_KEY"
  non_prod:
    vault_url: "https://your-non-prod-vault-url"
    app1:
      paths:
        - path: "kv/data/path/to/your/secret"
          format: "dotenv_plain"
          key: "dotenv"

vault:
  mount_point: "kv"
  formats:
    json:
      path_patterns: ["s3", "aws"]  # Patterns to auto-detect format
      aws_keys:  # Default AWS key names for JSON format
        access_key: "S3_ACCESS_KEY"
        secret_key: "S3_SECRET_KEY"
    dotenv_plain:
      path_patterns: ["env", "config"]
      aws_keys:
        access_key: "AWS_ACCESS_KEY"
        secret_key: "AWS_SECRET_KEY"
    dotenv_export:
      aws_keys:
        access_key: "AWS_ACCESS_KEY_ID"
        secret_key: "AWS_SECRET_ACCESS_KEY"
```

### Configuration Options 🔧

1. **Format Types**:
   - `json`: For structured JSON data
   - `dotenv_plain`: Simple key=value pairs
   - `dotenv_export`: Environment variables with export statements

2. **AWS Key Name Mapping**:
   - Path-specific mapping (highest priority)
   - Format-specific mapping (fallback)
   - Default mapping (lowest priority)

3. **Format Detection**:
   - Explicit format in path configuration
   - Pattern-based auto-detection
   - Content-based fallback detection

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
6. Show confirmation with:
   - Full access key for verification
   - Last 4 characters of secret key
   - Masked other sensitive values

### Supported Secret Types 🔑

1. AWS Credentials:
   - AWS Access Key ID (customizable name)
   - AWS Secret Access Key (customizable name)
   - Preserves existing key names during rotation

2. Environment Variables:
   - Any key-value pair in supported formats
   - Maintains format-specific structure
   - Preserves existing key names and values

## Error Handling 🚨

The script provides detailed error messages for:
- Authentication failures
- Permission issues
- Invalid paths
- Secret rotation failures
- Format validation errors

## Security Notes 🛡️

- Sensitive inputs are masked during entry
- Confirmation required before making changes
- Token and secret values are masked in logs
- Only last 4 characters of secret keys shown for verification
- Uses Vault's KV v2 engine for versioning 