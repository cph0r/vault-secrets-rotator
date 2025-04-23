# Secrets Rotate 🔄

A production-grade tool for rotating AWS credentials in HashiCorp Vault across different environments.

## Features ✨

- Environment-aware secret rotation (Testing, Non-Prod, Production)
- Secure handling of AWS credentials
- Dotenv-style secret management
- Comprehensive logging and error handling
- Path validation and security checks
- GitHub token authentication

## Installation 🚀

```bash
# Clone the repository
git clone https://github.com/your-org/secrets-rotate.git
cd secrets-rotate

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install the package
pip install -e .
```

## Usage 🎯

### List Available Environments

```bash
secrets-rotate --list-environments
```

### Test Authentication

```bash
secrets-rotate test-auth --environment testing
```

### Test Path Access

```bash
secrets-rotate test-path \
  --environment non-prod \
  --path "secret/data/your/path"
```

### Rotate AWS Credentials

```bash
secrets-rotate rotate \
  --environment prod \
  --path "secret/data/your/path" \
  --key "dotenv" \
  --aws-access-key "your-new-access-key" \
  --aws-secret-key "your-new-secret-key"
```

### Multiple Paths

```bash
secrets-rotate rotate \
  --environment non-prod \
  --paths "secret/data/path1" "secret/data/path2" \
  --aws-access-key "your-new-access-key" \
  --aws-secret-key "your-new-secret-key"
```

## Environment Setup 🌍

1. Create a `.env` file in your project root:
```env
VAULT_TOKEN=your-github-token
```

2. Ensure you have appropriate access to the Vault environments:
- Testing: https://vault-us-west-2-testing.c2fo.com/
- Non-Prod: https://vault-us-west-2-non-prod.c2fo.com/
- Production: https://vault-us-west-2.c2fo.com/

## Development 🛠️

### Project Structure

```
secrets_rotate/
├── core/           # Core functionality
│   ├── __init__.py
│   └── rotator.py  # VaultSecretRotator class
├── cli/            # CLI interface
│   ├── __init__.py
│   └── main.py     # Command-line handling
├── utils/          # Utility functions
│   ├── __init__.py
│   └── helpers.py  # Helper functions
├── config/         # Configuration
│   ├── __init__.py
│   └── settings.py # Configuration settings
└── tests/          # Test suite
    ├── __init__.py
    └── test_*.py   # Test files
```

### Running Tests

```bash
python -m pytest
```

## Security Considerations 🔒

- Never commit `.env` files
- Use environment-specific paths
- Always validate paths and keys
- Rotate production credentials with caution
- Use appropriate access controls in Vault

## Contributing 🤝

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License 📄

[Your License Here] 