# src/providers/base.py
# Base LLM provider class and shared HTTP retry utility for the NeuroOps Agent Platform.

import time
from abc import ABC, abstractmethod

import requests


# HTTP status codes that indicate a transient server-side problem worth retrying.
# 429 = rate limited, 5xx = server errors.
# 4xx errors other than 429 (auth failures, bad requests) are not retried —
# retrying them will not help.
_RETRYABLE_STATUS: frozenset[int] = frozenset({429, 500, 502, 503, 504})


def _post_with_retry(
    url: str,
    *,
    timeout: int,
    max_retries: int,
    **kwargs,
) -> requests.Response:
    """POST request with exponential-backoff retry for transient failures.

    Makes up to ``max_retries + 1`` total attempts. Between attempts, sleeps
    for ``2 ** attempt`` seconds (1 s, 2 s, …) so the maximum added latency
    with the default max_retries=2 is 3 seconds.

    Retries on:
      - ``requests.exceptions.Timeout``
      - ``requests.exceptions.ConnectionError``
      - HTTP status codes in ``_RETRYABLE_STATUS`` (429, 500, 502, 503, 504)

    Does NOT retry on:
      - HTTP 4xx except 429 (bad request, auth failure — retrying won't help)
      - Any other exception type

    On the final failed attempt the original exception is re-raised so callers
    receive a real exception rather than a silent swallowed error.

    Args:
        url: Target URL.
        timeout: Per-attempt connect + read timeout in seconds.
        max_retries: Number of additional attempts after the first (total = max_retries + 1).
        **kwargs: Passed through verbatim to ``requests.post``.

    Returns:
        ``requests.Response`` with a 2xx status code.

    Raises:
        requests.HTTPError: On non-retryable HTTP error or after exhausting retries.
        requests.Timeout: If every attempt times out.
        requests.ConnectionError: If every attempt fails to connect.
    """
    for attempt in range(max_retries + 1):
        try:
            r = requests.post(url, timeout=timeout, **kwargs)

            # Retryable HTTP status — sleep and loop unless this is the last attempt
            if r.status_code in _RETRYABLE_STATUS and attempt < max_retries:
                time.sleep(2 ** attempt)
                continue

            # Non-retryable 4xx, or retryable status on last attempt, or success:
            # raise_for_status() is a no-op on 2xx; raises HTTPError otherwise.
            r.raise_for_status()
            return r

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)

    # Unreachable — every code path either returns or raises inside the loop.
    raise RuntimeError("_post_with_retry: unexpected exit")  # pragma: no cover


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
