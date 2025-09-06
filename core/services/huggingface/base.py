"""
Base classes for Hugging Face services.

This module provides base classes for different types of Hugging Face interactions:
1. BaseHuggingFaceInferenceClient - for huggingface_hub.InferenceClient operations
2. BaseHuggingFaceAPIClient - for direct API calls with requests
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union

import requests
from tenacity import retry, stop_after_attempt, wait_exponential,retry_if_exception_type
from huggingface_hub import InferenceClient

from core.services.huggingface import constants
from core.logger import get_logger

logger = get_logger()


class BaseHuggingFaceInferenceClient(ABC):
    """
    Base class for Hugging Face services using the InferenceClient from huggingface_hub.

    This is ideal for:
    - Feature extraction / embeddings
    - Image processing
    - Audio processing
    - Other tasks supported by InferenceClient

    Subclasses should implement the specific functionality they need.
    """

    def __init__(self, model_id: str, api_token: Optional[str] = None):
        """
        Initialize the Hugging Face InferenceClient.

        Args:
            model_id: Hugging Face model identifier
            api_token: Optional API token (falls back to environment variable)
        """
        self.model_id = model_id

        # Get API token from parameter or environment
        if api_token is None:
            api_token = os.getenv("HUGGINGFACE_API_TOKEN")

        self.api_token = api_token

        # Initialize the InferenceClient
        self.client = InferenceClient(model=self.model_id, api_key=self.api_token)

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return a human-readable name for this service."""
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model_id": self.model_id,
            "service_name": self.service_name,
            "has_api_token": bool(self.api_token),
        }


class BaseHuggingFaceClassificationAPIClient(ABC):
    """
    Base class for Hugging Face services using direct API calls.

    This is ideal for:
    - Text classification
    It is advisable that any person attempting to use this class go through the Hugging Face API for text classification.

    Includes built-in retry logic, rate limiting, and error handling.
    """
   
    def __init__(
        self,
        model_id: Optional[str]=constants.DEFAULT_CLASSIFICATION_MODEL_ID,
        api_token: Optional[str]=os.getenv("HUGGINGFACE_API_TOKEN"),
    ):
        """
        Initialize a Hugging Face classification client.

        Args:
            model_id (Optional[str]): Model identifier, e.g. "facebook/bart-large-mnli". 
                If not provided, defaults to `DEFAULT_CLASSIFICATION_MODEL_ID` from `constants.py`.
            api_token (Optional[str]): Hugging Face API token. If not provided, will attempt 
                to load from the environment variable `HUGGINGFACE_API_TOKEN`.
            timeout (int): Request timeout in seconds. Defaults to 30.
            
        """
    
        self.model_id = model_id or constants.DEFAULT_CLASSIFICATION_MODEL_ID
        self.api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        self.extra = kwargs

        if not self.model_id:
            raise ValueError("Missing model_id. Provide one or set DEFAULT_CLASSIFICATION_MODEL_ID.")
        if not self.api_token:
            raise EnvironmentError("Missing api_token. Set HUGGINGFACE_API_TOKEN in env or pass explicitly.")
            
        self.api_url = f"{constants.HUGGINGFACE_API_BASE_URL}/{self.model_id}"
        self.headers = {"Content-Type": "application/json"}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

        # Track last request time for rate limiting
        self._last_request_time = 0


    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return a human-readable name for this service."""
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=(
            retry_if_exception_type(requests.exceptions.Timeout) |
            retry_if_exception_type(requests.exceptions.RequestException) |
            retry_if_exception_type(Exception)  
        ),
        reraise=True  # re-raise the last exception after retries are exhausted
    )
    def _make_api_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Hugging Face API with automatic retry logic.

        Args:
            payload: Request payload

        Returns:
            API response data
        """
        self._rate_limit()

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            
            elif response.status_code in {503, 429}:
               
                raise Exception(f"API returned {response.status_code}, retrying...")

            else:
                response.raise_for_status()

        except requests.exceptions.Timeout as e:
            logger.warning(
                "API request timeout, retrying...",
                extra={"model_id": self.api_url}
            )
            raise e

        except requests.exceptions.RequestException as e:
            logger.warning(
                "Request exception occurred, retrying...",
                extra={"error": str(e), "model_id": self.api_url}
            )
            raise e

        except Exception as e:
            logger.warning(
                "Unexpected exception, retrying...",
                extra={"error": str(e), "model_id": self.api_url}
            )
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=(
            retry_if_exception_type(requests.exceptions.Timeout) |
            retry_if_exception_type(requests.exceptions.RequestException) |
            retry_if_exception_type(Exception)  
        ),
        reraise=True  # re-raise the last exception after retries are exhausted
    )
    def is_ready(self) -> bool:
        """
        Check if the API is accessible and the model is ready.

        Returns:
            True if the API is ready, False otherwise
        """
        try:
            test_payload = self._get_health_check_payload()
            result = self._make_api_request(test_payload)
            return bool(result)
        except Exception as e:
            logger.error(
                "Hugging Face API not ready", error=str(e), model_id=self.model_id
            )
            raise e

    @abstractmethod
    def _get_health_check_payload(self) -> Dict[str, Any]:
        """
        Return a test payload for health checks.

        Each service should implement this to provide an appropriate test payload.
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model and configuration."""
        return {
            "model_id": self.model_id,
            "service_name": self.service_name,
            "api_url": self.api_url,
            "has_api_token": bool(self.api_token),
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
