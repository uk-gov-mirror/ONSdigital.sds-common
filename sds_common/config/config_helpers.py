import os

from sds_common.models.config_errors import EnvironmentVariableError


class ConfigHelpers:
    @staticmethod
    def can_cast_to_bool(value: str) -> bool:
        """
        Checks if a string value can be cast to a bool value when made lowercase.

        :param value: env value
        """
        return value.lower() in ["true", "false"]

    @staticmethod
    def get_bool_value(value: str) -> bool:
        """
        Returns true if the lowercase string value is true, otherwise returns false.

        :param value: env value
        """
        return value.lower() == "true"

    @staticmethod
    def format_value(value: str) -> str | bool:
        """
        Formats the value to return a boolean if it casts, otherwise return a string.

        :param value: environment variable value
        :return str | bool: formatted value
        """
        return (
            ConfigHelpers.get_bool_value(value)
            if ConfigHelpers.can_cast_to_bool(value)
            else value
        )

    @staticmethod
    def get_value_from_env(
        env_value: str, default_value: str | None = None
    ) -> str | bool:
        """
        Returns the value of the specified environment variable, or the default if provided.
        If an environment variable or default value are not set an exception is raised.

        :param env_value: value to check environment for
        :param default_value: optional argument to allow defaulting of values
        :return str: the environment value corresponding to the input
        :raises EnvironmentVariableError: if the environment variable is not set and no default value is provided
        """
        value = os.environ.get(env_value)

        if value is not None:
            return ConfigHelpers.format_value(value)

        if default_value is not None:
            return default_value

        raise EnvironmentVariableError(env_value)
