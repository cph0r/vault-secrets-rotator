#!/usr/bin/env python3

import hvac
import os
from dotenv import load_dotenv
import logging
from typing import List
import json
import sys
import argparse
from vault_tests import test_setup, test_path_access
from vault_utils import validate_path, validate_key, parse_dotenv_content, update_dotenv_content

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VaultSecretRotator:
    def __init__(self):
        load_dotenv()
        self.vault_addr = os.getenv('VAULT_ADDR')
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.vault_addr or not self.github_token:
            raise ValueError("Missing required environment variables! 🚨 VAULT_ADDR and GITHUB_TOKEN are required!")
        
        self.client = hvac.Client(url=self.vault_addr)
        self._authenticate()

    def _authenticate(self):
        try:
            self.client.auth.github.login(token=self.github_token)
            logger.info("Authentication successful! Your GitHub token actually works! 🎉")
        except Exception as e:
            logger.error(f"Authentication failed! Did you forget to pay your GitHub bill? 😅 Error: {str(e)}")
            raise

    def rotate_secret(self, path: str, key: str, new_value: str = None) -> dict:
        """
        Rotate a secret at the specified path. If it's a dotenv-style secret,
        handle it appropriately! 💃
        """
        try:
            validate_path(path)
            validate_key(key)
            
            # Read existing secret
            try:
                secret = self.client.secrets.kv.v2.read_secret_version(path=path)
                current_data = secret['data']['data']
            except Exception as e:
                logger.error(f"Failed to read secret at {path}! Is it hiding? 🕵️‍♂️ Error: {str(e)}")
                raise

            # Handle dotenv-style secrets
            if key == 'dotenv' and isinstance(current_data.get(key), str):
                if not new_value:
                    raise ValueError("New value is required for dotenv updates! Don't leave me hanging! 🤷‍♂️")
                
                current_content = current_data[key]
                updates = json.loads(new_value)  # Expect a JSON string of key-value pairs
                
                updated_content, old_values = update_dotenv_content(current_content, updates)
                current_data[key] = updated_content
                
                logger.info(f"Updated dotenv values: {json.dumps(old_values, indent=2)} 📝")
            else:
                # Regular secret rotation
                old_value = current_data.get(key)
                current_data[key] = new_value or self._generate_secret()
                logger.info(f"Rotated secret {key} from {old_value} to {current_data[key]} 🔄")

            # Write updated secret back
            try:
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=current_data,
                )
                logger.info(f"Successfully updated secret at {path}! Mission accomplished! 🎯")
                return {"old_value": old_value, "new_value": current_data[key]}
            except Exception as e:
                logger.error(f"Failed to write secret! Did the vault door get stuck? 🚪 Error: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Failed to rotate secret! Time to panic! 😱 Error: {str(e)}")
            raise

    def _generate_secret(self, length: int = 32) -> str:
        """Generate a random secret. Because creativity is hard! 🎲"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    parser = argparse.ArgumentParser(description="Rotate your Vault secrets with style! 💃")
    parser.add_argument('command', choices=['test-auth', 'test-path', 'rotate'],
                      help='Command to execute (test-auth, test-path, or rotate)')
    parser.add_argument('path', nargs='?', help='Path to the secret')
    parser.add_argument('key', nargs='?', help='Key to rotate')
    parser.add_argument('value', nargs='?', help='New value (optional)')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'test-auth':
            test_setup()
        elif args.command == 'test-path':
            if not args.path:
                raise ValueError("Path argument is required! Don't leave me guessing! 🤔")
            test_path_access(args.path)
        elif args.command == 'rotate':
            if not args.path or not args.key:
                raise ValueError("Path and key arguments are required! I'm not a mind reader! 🔮")
            rotator = VaultSecretRotator()
            rotator.rotate_secret(args.path, args.key, args.value)
    except Exception as e:
        logger.error(f"Operation failed! Time to update your resume? 😅 Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()