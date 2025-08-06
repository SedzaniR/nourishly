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

from huggingface_hub import InferenceClient
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

    def __init__(self, model_id: str, api_token: Optional[str] = None, **kwargs):
        """
        Initialize the Hugging Face InferenceClient.

        Args:
            model_id: Hugging Face model identifier
            api_token: Optional API token (falls back to environment variable)
            **kwargs: Additional configuration
        """
        self.model_id = model_id

        # Get API token from parameter or environment
        if api_token is None:
            api_token = os.getenv("HUGGINGFACE_API_TOKEN")

        self.api_token = api_token

        # Initialize the InferenceClient
        self.client = InferenceClient(model=self.model_id, api_key=self.api_token)

        logger.info(
            "Initialized Hugging Face InferenceClient",
            model_id=self.model_id,
            has_api_token=bool(self.api_token),
        )

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


class BaseHuggingFaceAPIClient(ABC):
    """
    Base class for Hugging Face services using direct API calls.

    This is ideal for:
    - Text classification
    - Text generation
    - Custom inference endpoints
    - Tasks requiring fine-grained control over API calls

    Includes built-in retry logic, rate limiting, and error handling.
    """

    HUGGINGFACE_API_BASE_URL = "https://api-inference.huggingface.co/models"

    def __init__(
        self,
        model_id: str,
        api_token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.1,
        **kwargs,
    ):
        """
        Initialize the Hugging Face API client.

        Args:
            model_id: Hugging Face model identifier
            api_token: Optional API token (falls back to environment variable)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            rate_limit_delay: Minimum delay between requests in seconds
            **kwargs: Additional configuration
        """
        self.model_id = model_id

        # Get API token from parameter or environment
        if api_token is None:
            api_token = os.getenv("HUGGINGFACE_API_TOKEN")

        self.api_token = api_token

        # API configuration
        self.api_url = f"{self.HUGGINGFACE_API_BASE_URL}/{self.model_id}"
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay

        # Setup headers
        self.headers = {"Content-Type": "application/json"}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

        # Track last request time for rate limiting
        self._last_request_time = 0

        logger.info(
            "Initialized Hugging Face API client",
            model_id=self.model_id,
            has_api_token=bool(self.api_token),
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return a human-readable name for this service."""
        pass

    def _rate_limit(self) -> None:
        """Implement rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug("Rate limiting API request", sleep_time=sleep_time)
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _make_api_request(
        self, payload: Dict[str, Any], retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Make a request to the Hugging Face API with retry logic.

        Args:
            payload: Request payload
            retry_count: Current retry attempt

        Returns:
            API response data, or None if the request fails
        """
        self._rate_limit()

        try:
            response = requests.post(
                self.api_url, headers=self.headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                # Model is loading, wait and retry
                if retry_count < self.max_retries:
                    wait_time = self.retry_delay * (retry_count + 1)
                    logger.warning(
                        "Model is loading, retrying",
                        retry_count=retry_count,
                        wait_time=wait_time,
                        model_id=self.model_id,
                    )
                    time.sleep(wait_time)
                    return self._make_api_request(payload, retry_count + 1)
                else:
                    logger.error(
                        "Model failed to load after maximum retries",
                        model_id=self.model_id,
                        max_retries=self.max_retries,
                    )
                    return None
            elif response.status_code == 429:
                # Rate limited, wait and retry
                if retry_count < self.max_retries:
                    wait_time = self.retry_delay * (retry_count + 1) * 2
                    logger.warning(
                        "Rate limited, retrying",
                        retry_count=retry_count,
                        wait_time=wait_time,
                        model_id=self.model_id,
                    )
                    time.sleep(wait_time)
                    return self._make_api_request(payload, retry_count + 1)
                else:
                    logger.error(
                        "Rate limit exceeded, maximum retries reached",
                        model_id=self.model_id,
                        max_retries=self.max_retries,
                    )
                    return None
            else:
                logger.error(
                    "Hugging Face API request failed",
                    status_code=response.status_code,
                    error_text=response.text,
                    model_id=self.model_id,
                )
                return None

        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                logger.warning(
                    "API request timeout, retrying",
                    retry_count=retry_count,
                    model_id=self.model_id,
                )
                time.sleep(self.retry_delay)
                return self._make_api_request(payload, retry_count + 1)
            else:
                logger.error(
                    "API request timeout after maximum retries",
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    model_id=self.model_id,
                )
                return None
        except requests.exceptions.RequestException as e:
            logger.error(
                "API request exception",
                error=str(e),
                retry_count=retry_count,
                model_id=self.model_id,
            )
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self._make_api_request(payload, retry_count + 1)
            else:
                logger.error(
                    "API request failed after maximum retries",
                    original_error=str(e),
                    max_retries=self.max_retries,
                    model_id=self.model_id,
                )
                return None
        except Exception as e:
            logger.error(
                "Unexpected API request exception",
                error=str(e),
                retry_count=retry_count,
                model_id=self.model_id,
            )
            return None

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
            return False

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
            "retry_delay": self.retry_delay,
            "rate_limit_delay": self.rate_limit_delay,
        }
