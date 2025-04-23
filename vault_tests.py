import logging
from typing import List, Optional
import hvac
import os
from dotenv import load_dotenv
from vault_utils import validate_vault_path, format_error_message

# Set up logging because testing without logs is like dancing without music! 🎵
logger = logging.getLogger(__name__)

class VaultTester:
    def __init__(self):
        """Initialize our test suite because we're professional like that! 🧪"""
        load_dotenv()
        
        self.vault_addr = os.getenv('VAULT_ADDR')
        self.github_token = os.getenv('VAULT_TOKEN')
        
        if not all([self.vault_addr, self.github_token]):
            raise ValueError("Missing credentials! Check your .env file! 🔍")
            
        self.client = hvac.Client(url=self.vault_addr)
        
    def test_auth(self) -> bool:
        """Test if we can authenticate to Vault using GitHub 🔐"""
        try:
            self.client.auth.github.login(token=self.github_token)
            if self.client.is_authenticated():
                logger.info("Authentication successful! Your GitHub token actually works! 🎉")
                return True
            else:
                logger.error("Authentication failed! Is your GitHub token still valid? 🔌")
                return False
        except Exception as e:
            logger.error(format_error_message(e))
            return False
            
    def test_path_access(self, path: str) -> bool:
        """Test read and write access to a path 🔍"""
        try:
            # First authenticate
            if not self.test_auth():
                return False
                
            # Validate path format
            is_valid, error_msg = validate_vault_path(path)
            if not is_valid:
                logger.error(error_msg)
                return False
            
            # Test read
            logger.info(f"Testing read access to path: {path} 👀")
            secret = self.client.read(path)
            if not secret or 'data' not in secret:
                logger.error(f"Cannot read secret at {path}! Do you even have access? 🤔")
                return False
                
            # Test write by writing the same data back
            logger.info(f"Testing write access to path: {path} ✍️")
            current_data = secret['data'].get('data', {})
            self.client.write(path, data=current_data)
            
            logger.info(f"Successfully tested read/write access to {path}! You're a star! ⭐")
            return True
            
        except Exception as e:
            logger.error(format_error_message(e))
            return False

def test_setup() -> bool:
    """Run the authentication test 🎭"""
    try:
        tester = VaultTester()
        return tester.test_auth()
    except Exception as e:
        logger.error(format_error_message(e))
        return False

def test_path_access(path: str) -> bool:
    """Run the path access test 🎯"""
    try:
        tester = VaultTester()
        return tester.test_path_access(path)
    except Exception as e:
        logger.error(format_error_message(e))
        return False

# Add some fancy test runners because we're extra like that ✨
def run_all_tests(paths: List[str] = None) -> bool:
    """Run all tests because we're thorough like that! 🎭"""
    logger.info("Starting test suite - hold onto your bits! 🎪")
    
    # Test authentication
    auth_success = test_setup()
    if not auth_success:
        logger.error("Authentication test failed! Everything else is pointless! 😭")
        return False
        
    # Test paths if provided
    if paths:
        for path in paths:
            logger.info(f"Testing path: {path} 🎯")
            if not test_path_access(path):
                logger.error(f"Path test failed for {path}! 💔")
                return False
                
    logger.info("All tests passed! You're a testing genius! 🎉")
    return True 