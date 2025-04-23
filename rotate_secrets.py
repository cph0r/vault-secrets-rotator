import hvac
import os
from dotenv import load_dotenv
import logging
from typing import Dict, List
import json
import sys
import argparse
from vault_tests import test_setup, test_path_access
from vault_utils import (
    parse_dotenv_content,
    update_dotenv_content,
    validate_vault_path,
    get_secret_keys
)

logging.basicConfig(level=logging.INFO)

class VaultSecretRotator:
    def __init__(self):
        """
        Initialize the VaultSecretRotator.
        Like a superhero getting suited up! 🦸‍♂️
        """
        load_dotenv()
        self.vault_addr = os.getenv('VAULT_ADDR')
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.vault_addr or not self.github_token:
            raise ValueError("Missing credentials! Did you forget your superhero costume? 🦹")
            
        self.client = hvac.Client(url=self.vault_addr)
        self._authenticate()

    def _authenticate(self):
        """
        Authenticate with Vault using GitHub token.
        Like showing your VIP pass at the club! 🎟️
        """
        try:
            self.client.auth.github.login(token=self.github_token)
            logging.info("Authentication successful! Your GitHub token actually works! 🎉")
        except Exception as e:
            logging.error(f"Authentication failed! Looks like we're not on the guest list: {str(e)} 😭")
            sys.exit(1)

    def rotate_secret(self, path: str, key: str, new_value: str = None):
        """
        Rotate a secret at the specified path.
        Like changing your password, but way more fun! 🔄
        """
        try:
            path = validate_vault_path(path)
            
            # Read current secret
            try:
                secret = self.client.secrets.kv.v2.read_secret_version(path=path)
                current_data = secret['data']['data']
            except Exception as e:
                logging.error(f"Failed to read secret at {path}. Are we looking in the right place? 🤔")
                return None, None

            if key not in current_data:
                logging.error(f"Key '{key}' not found. Did it go on vacation? 🏖️")
                return None, None

            current_value = current_data[key]
            
            # Handle dotenv-style content
            if '\n' in str(current_value):
                if not new_value:
                    logging.error("New value required for dotenv content! Don't leave us hanging! 🎭")
                    return None, None
                    
                updates = {}
                if isinstance(new_value, str):
                    try:
                        updates = json.loads(new_value)
                    except json.JSONDecodeError:
                        logging.error("Invalid JSON for updates! Did a cat walk on your keyboard? 🐱")
                        return None, None
                elif isinstance(new_value, dict):
                    updates = new_value
                
                updated_content, old_values = update_dotenv_content(current_value, updates)
                current_data[key] = updated_content
                
                try:
                    self.client.secrets.kv.v2.create_or_update_secret(
                        path=path,
                        secret=current_data
                    )
                    logging.info(f"Updated dotenv content at {path}! Old values: {old_values} 📝")
                    return old_values, updates
                except Exception as e:
                    logging.error(f"Failed to update secret: {str(e)} 💔")
                    return None, None
            
            # Handle regular key-value pairs
            else:
                if not new_value:
                    logging.error("New value required! Don't be shy! 🙈")
                    return None, None
                    
                old_value = current_data[key]
                current_data[key] = new_value
                
                try:
                    self.client.secrets.kv.v2.create_or_update_secret(
                        path=path,
                        secret=current_data
                    )
                    logging.info(f"Rotated secret at {path}! Old value: {old_value} 🔄")
                    return old_value, new_value
                except Exception as e:
                    logging.error(f"Failed to rotate secret: {str(e)} 💔")
                    return None, None
                    
        except Exception as e:
            logging.error(f"Failed to rotate secret: {str(e)} 😱")
            return None, None

def main():
    parser = argparse.ArgumentParser(description="Rotate secrets in HashiCorp Vault! 🔐")
    parser.add_argument('command', choices=['test-auth', 'test-path', 'rotate'],
                      help='Command to execute')
    parser.add_argument('--path', help='Secret path')
    parser.add_argument('--key', help='Secret key to rotate')
    parser.add_argument('--value', help='New value for the secret')
    
    args = parser.parse_args()
    
    if args.command == 'test-auth':
        test_setup()
    elif args.command == 'test-path':
        if not args.path:
            logging.error("Path required for testing! Don't leave us in the dark! 🔦")
            sys.exit(1)
        test_path_access(args.path)
    elif args.command == 'rotate':
        if not args.path or not args.key:
            logging.error("Path and key required for rotation! We're not mind readers! 🔮")
            sys.exit(1)
        rotator = VaultSecretRotator()
        old_value, new_value = rotator.rotate_secret(args.path, args.key, args.value)
        if old_value is None or new_value is None:
            sys.exit(1)

if __name__ == '__main__':
    main()