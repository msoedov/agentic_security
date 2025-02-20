import tomli
from loguru import logger


class CfgMixin:
    config = {}
    default_path = "agentic_security.toml"

    def get_or_create_config(self) -> bool:
        if not self.has_local_config():
            self.generate_default_cfg()
            return False
        self.load_config(self.default_path)
        return True

    def has_local_config(self):
        try:
            with open(self.default_path):
                return True
        except FileNotFoundError:
            return False

    @classmethod
    def load_config(cls, config_path: str):
        """
        Load configuration from a TOML file and store it in the class variable.

        Args:
            config_path (str): Path to the TOML configuration file.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            toml.TomlDecodeError: If the configuration file has syntax errors.
        """
        try:
            with open(config_path, "rb") as config_file:
                cls.config = tomli.load(config_file)
                logger.info(f"Configuration loaded successfully from {config_path}.")
        except FileNotFoundError:
            logger.error(f"Configuration file {config_path} not found.")
            raise
        except Exception as e:
            logger.error(f"Error parsing TOML configuration: {e}")
            raise

    @classmethod
    def get_config_value(cls, key: str, default=None):
        """
        Retrieve a configuration value by key from the loaded configuration.

        Args:
            key (str): Dot-separated key path to the configuration value (e.g., 'general.maxBudget').
            default: Default value if the key is not found.

        Returns:
            The configuration value if found, otherwise the default value.
        """
        keys = key.split(".")
        value = cls.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
