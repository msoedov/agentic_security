from fastapi import Depends

from agentic_security.config import CfgMixin


class InMemorySecrets:
    def __init__(self):
        self.secrets = {}
        self.config = CfgMixin()
        self.config.get_or_create_config()
        self.secrets = self.config.config.get("secrets", {})

    def set_secret(self, key: str, value: str):
        self.secrets[key] = value

    def get_secret(self, key: str) -> str:
        return self.secrets.get(key, None)


# Dependency
def get_in_memory_secrets() -> InMemorySecrets:
    return InMemorySecrets()


# Example usage in a FastAPI route
# @app.get("/some-endpoint")
# async def some_endpoint(secrets: InMemorySecrets = Depends(get_in_memory_secrets)):
#     # Use secrets here
#     pass
