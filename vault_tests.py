import hvac
import os
from dotenv import load_dotenv
import logging

class VaultTester:
    def __init__(self):
        load_dotenv()
        self.vault_addr = os.getenv('VAULT_ADDR')
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.vault_addr or not self.github_token:
            raise ValueError("Missing environment variables! Did you forget to fill out your .env file? 🤦‍♂️")
        
        self.client = hvac.Client(url=self.vault_addr)
        self.logger = logging.getLogger(__name__)

    def test_auth(self) -> bool:
        """
        Test authentication with Vault using GitHub token.
        Returns True if successful, False otherwise.
        """
        try:
            self.client.auth.github.login(token=self.github_token)
            self.logger.info("Authentication successful! Your GitHub token actually works! 🎉")
            return True
        except Exception as e:
            self.logger.error(f"Authentication failed! Did you anger the GitHub gods? 😅 Error: {str(e)}")
            return False

    def test_path_access(self, path: str) -> bool:
        """
        Test read/write access to a specific path in Vault.
        Returns True if both read and write are successful, False otherwise.
        """
        if not path:
            raise ValueError("Path cannot be empty! What am I supposed to test, the void? 🌌")

        # Normalize path
        if path.startswith('secret/'):
            path = path.replace('secret/', '', 1)
        elif path.startswith('kv/'):
            path = path.replace('kv/', '', 1)

        if not path.startswith('data/'):
            path = f"data/{path}"

        test_key = "test_access_key"
        test_value = "If you can read this, you have access! 🎯"

        try:
            # Try to read existing secret
            try:
                self.client.secrets.kv.v2.read_secret_version(path=path)
                self.logger.info(f"Successfully read from {path}! 📖")
            except Exception as e:
                self.logger.warning(f"Couldn't read from {path}. Either it doesn't exist or you don't have access! 🤔 Error: {str(e)}")

            # Try to write a test secret
            try:
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret={test_key: test_value},
                )
                self.logger.info(f"Successfully wrote to {path}! ✍️")
                return True
            except Exception as e:
                self.logger.error(f"Failed to write to {path}! No party for you! 🚫 Error: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"Path access test failed! Time to check those permissions! 🔑 Error: {str(e)}")
            return False

def test_setup() -> bool:
    """Test Vault authentication setup"""
    tester = VaultTester()
    return tester.test_auth()

def test_path_access(path: str) -> bool:
    """Test access to a specific path"""
    tester = VaultTester()
    if not tester.test_auth():
        return False
    return tester.test_path_access(path)