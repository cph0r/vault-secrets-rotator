# 🔐 Vault Secrets Rotator

Because your secrets deserve a makeover every now and then! 💅

## 🌟 Features

- Authenticate with HashiCorp Vault using GitHub tokens (because who doesn't love OAuth?)
- Rotate secrets like a pro DJ 🎧
- Handle dotenv-style secrets with more grace than a ballet dancer
- Test your Vault access without breaking a sweat 💪
- Logging that's more informative than your chatty neighbor

## 🚀 Getting Started

### Prerequisites

- Python 3.x (because we're not savages)
- HashiCorp Vault instance (duh!)
- GitHub token with the right permissions (don't be stingy with those scopes!)
- A sense of humor (required)

### Installation

1. Clone this repository (it won't bite):
```bash
git clone https://github.com/cph0r/vault-secrets-rotator.git
cd vault-secrets-rotator
```

2. Set up your environment variables (because hardcoding is so 2010):
```bash
export VAULT_ADDR="your-vault-address"
export GITHUB_TOKEN="your-github-token"
```

## 🎯 Usage

### Testing Authentication

```bash
python3 rotate_secrets.py test-auth
```

### Testing Path Access

```bash
python3 rotate_secrets.py test-path "your/vault/path"
```

### Rotating Secrets

```bash
python3 rotate_secrets.py rotate "your/vault/path" "your-secret-key" "new-value"
```

## 🧪 Testing

Run the test suite (it's more reliable than your ex):
```bash
python3 test_runner.py
```

## 📚 File Structure

- `rotate_secrets.py`: The star of the show 🌟
- `vault_tests.py`: Testing suite (because we're professionals)
- `vault_utils.py`: Utility functions (the unsung heroes)

## 🤝 Contributing

PRs are welcome! Just make sure your code is as fabulous as ours! ✨

## 📝 License

MIT - Because sharing is caring! 🤗

## ⚠️ Disclaimer

No secrets were harmed in the making of this tool. However, we can't promise the same for your sanity while debugging Vault permissions! 😅