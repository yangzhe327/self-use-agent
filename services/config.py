import os
from typing import Optional
from exceptions.project_exceptions import ConfigurationError


class Config:
    """
    Configuration class for the application
    """
    def __init__(self):
        self._api_key: Optional[str] = None
        self._model_name: str = "qwen3-coder-plus"
        self._max_retries: int = 3
        self._timeout: int = 30

    @property
    def api_key(self) -> str:
        """
        Get the DashScope API key
        """
        if self._api_key is None:
            self._api_key = os.getenv("DASHSCOPE_API_KEY")
            if self._api_key is None:
                raise ConfigurationError(
                    "DashScope API key not found. "
                    "Please set the DASHSCOPE_API_KEY environment variable."
                )
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        """
        Set the DashScope API key
        """
        self._api_key = value

    @property
    def model_name(self) -> str:
        """
        Get the model name for DashScope API
        """
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        """
        Set the model name for DashScope API
        """
        self._model_name = value

    @property
    def max_retries(self) -> int:
        """
        Get the maximum number of retries for API calls
        """
        return self._max_retries

    @max_retries.setter
    def max_retries(self, value: int):
        """
        Set the maximum number of retries for API calls
        """
        self._max_retries = value

    @property
    def timeout(self) -> int:
        """
        Get the timeout for API calls
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value: int):
        """
        Set the timeout for API calls
        """
        self._timeout = value