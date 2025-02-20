from agentic_security.dependencies import InMemorySecrets, get_in_memory_secrets


def test_in_memory_secrets():
    secrets = InMemorySecrets()
    secrets.set_secret("api_key", "12345")
    assert secrets.get_secret("api_key") == "12345"
    assert secrets.get_secret("non_existent_key") is None


def test_get_in_memory_secrets():
    secrets = get_in_memory_secrets()
    assert isinstance(secrets, InMemorySecrets)
    secrets.set_secret("token", "abcde")
    assert secrets.get_secret("token") == "abcde"
