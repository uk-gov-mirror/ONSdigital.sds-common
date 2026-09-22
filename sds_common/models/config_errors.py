from __future__ import annotations
class EnvironmentVariableError(Exception):
    """Raised when a required environment variable is not set and no default is provided."""

    def __init__(self, variable_name: str) -> None:
        self.variable_name = variable_name
        super().__init__(
            f"The environment variable '{variable_name}' must be set to proceed."
        )
