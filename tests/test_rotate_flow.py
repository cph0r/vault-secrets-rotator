import pytest
import yaml
import rotate_secrets
import utils
from types import SimpleNamespace


def test_full_flow(monkeypatch, capsys, tmp_path):
    # Prepare a temporary config.yaml
    config_data = {
        'vault': {'address': 'http://example.com', 'mount_point': 'secret'},
        'environments': {
            'prod': {'Helios': {'paths': ['secret/data/helios/app1']}}
        }
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data))

    # Change working directory to where config.yaml is
    monkeypatch.chdir(tmp_path)

    # Simulate user inputs
    inputs = iter([
        'dummy-token',       # GitHub PAT token
        'prod',              # environment selection
        'Helios',            # application selection
        'AWS secret keys',   # secret type
        'AKIATEST',          # new AWS access key ID
        'SECRETTEST',        # new AWS secret access key
        'y',                 # confirmation
    ])
    monkeypatch.setattr(utils, 'prompt_user', lambda *args, **kwargs: next(inputs))
    # Stub Vault client operations
    fake_client = SimpleNamespace()
    monkeypatch.setattr(utils, 'init_vault_client', lambda token, cfg: fake_client)
    monkeypatch.setattr(utils, 'check_login', lambda client: True)
    monkeypatch.setattr(utils, 'check_paths', lambda client, mount, paths: {paths[0]: True})

    rotated = []
    monkeypatch.setattr(utils, 'rotate_secret_kv', lambda c, m, p, k, v: rotated.append((p, k, v)))

    # Run the main script
    rotate_secrets.main()

    # Capture outputs (both stdout and stderr)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    # Verify rotation calls
    assert rotated == [
        ('secret/data/helios/app1', 'AWS_ACCESS_KEY_ID', 'AKIATEST'),
        ('secret/data/helios/app1', 'AWS_SECRET_ACCESS_KEY', 'SECRETTEST'),
    ]
    # Verify success message
    assert 'Secrets rotated successfully' in output 