import yaml
import pytest
import utils

from utils import (
    load_config,
    init_vault_client,
    check_login,
    check_paths,
    prompt_user,
    rotate_secret_kv,
    confirm_changes,
)

# Dummy classes for simulating Vault client behavior
class DummyV2:
    def __init__(self, data_map):
        self.data_map = data_map
        self.updated = None

    def read_secret_version(self, path):
        if path in self.data_map:
            return {'data': {'data': self.data_map[path]}}
        raise Exception("not found")

    def create_or_update_secret(self, path, secret):
        self.updated = (path, secret)

class DummyClient:
    def __init__(self, auth, data_map):
        self._auth = auth
        self.secrets = type('S', (), {})()
        self.secrets.kv = type('Q', (), {})()
        self.secrets.kv.v2 = DummyV2(data_map)

    def is_authenticated(self):
        return self._auth


def test_load_config(tmp_path):
    # Prepare a temporary YAML config file
    config_file = tmp_path / "test.yaml"
    content = {'a': 1, 'b': 'two'}
    config_file.write_text(yaml.dump(content))

    # Load config and verify
    result = load_config(str(config_file))
    assert result == content


def test_init_vault_client(monkeypatch):
    # Monkeypatch hvac.Client to capture parameters
    called = {}
    def fake_client(**kwargs):
        called.update(kwargs)
        return 'fake-client'
    monkeypatch.setattr(utils.hvac, 'Client', fake_client)

    cfg = {'vault': {'address': 'http://vault.example.com', 'mount_point': 'secret'}}
    client = init_vault_client('tok123', cfg)

    assert client == 'fake-client'
    assert called == {'url': 'http://vault.example.com', 'token': 'tok123'}


def test_check_login_and_paths():
    # Create clients for authenticated and unauthenticated
    client_true = DummyClient(auth=True, data_map={})
    client_false = DummyClient(auth=False, data_map={})

    assert check_login(client_true)
    assert not check_login(client_false)

    # Test path access checking
    data_map = {'valid': {'foo': 'bar'}}
    client = DummyClient(auth=True, data_map=data_map)
    paths = ['secret/data/valid', 'secret/data/invalid']
    results = check_paths(client, 'secret', paths)
    assert results['secret/data/valid']
    assert not results['secret/data/invalid']


def test_prompt_user_no_choices(monkeypatch, capsys):
    # Simulate user input without choices
    monkeypatch.setattr('builtins.input', lambda prompt='': 'value1')
    result = prompt_user("Enter value")
    assert result == 'value1'


def test_prompt_user_with_choices(monkeypatch, capsys):
    # Simulate user selecting the second option
    inputs = iter(['2'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))

    choices = ['opt1', 'opt2', 'opt3']
    result = prompt_user("Choose option", choices)
    output = capsys.readouterr().out

    assert "Choose option" in output
    assert '1. opt1' in output
    assert '2. opt2' in output
    assert result == 'opt2'


def test_rotate_secret_kv():
    # Prepare dummy client with initial secret
    data_map = {'path1': {'key1': 'old'}}
    client = DummyClient(auth=True, data_map=data_map)

    # Rotate the secret
    rotate_secret_kv(client, 'secret', 'secret/data/path1', 'key1', 'new')  
    # Verify update was called correctly
    expected_path = 'path1'
    expected_secret = {'key1': 'new'}
    assert client.secrets.kv.v2.updated == (expected_path, expected_secret)


def test_confirm_changes(monkeypatch, capsys):
    changes = {'x': '1', 'y': '2'}

    # User confirms
    monkeypatch.setattr('builtins.input', lambda prompt='': 'y')
    assert confirm_changes(changes)

    # User declines
    monkeypatch.setattr('builtins.input', lambda prompt='': 'n')
    assert not confirm_changes(changes) 