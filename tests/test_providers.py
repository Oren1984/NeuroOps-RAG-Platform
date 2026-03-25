# tests/test_providers.py
# Tests for LLM provider hardening: stubs, timeouts, retry logic, error handling.

from unittest.mock import MagicMock, call, patch

import pytest
import requests as req_lib


# ---------------------------------------------------------------------------
# _post_with_retry — unit tests for the shared retry utility
# ---------------------------------------------------------------------------

class TestPostWithRetry:
    """Tests for the shared _post_with_retry helper in src/providers/base.py."""

    def _make_response(self, status_code: int) -> MagicMock:
        r = MagicMock()
        r.status_code = status_code
        if status_code >= 400:
            r.raise_for_status.side_effect = req_lib.HTTPError(
                response=MagicMock(status_code=status_code)
            )
        else:
            r.raise_for_status = MagicMock()
        return r

    def test_success_on_first_attempt(self):
        """Returns response immediately on 200, no sleep."""
        from src.providers.base import _post_with_retry

        mock_resp = self._make_response(200)
        with patch("src.providers.base.requests.post", return_value=mock_resp) as mock_post, \
             patch("src.providers.base.time.sleep") as mock_sleep:
            result = _post_with_retry("http://x", timeout=5, max_retries=2, json={})

        assert result is mock_resp
        assert mock_post.call_count == 1
        mock_sleep.assert_not_called()

    def test_retries_on_429_then_succeeds(self):
        """Retries after 429, returns response on next success."""
        from src.providers.base import _post_with_retry

        mock_429 = self._make_response(429)
        mock_200 = self._make_response(200)

        with patch("src.providers.base.requests.post", side_effect=[mock_429, mock_200]) as mock_post, \
             patch("src.providers.base.time.sleep") as mock_sleep:
            result = _post_with_retry("http://x", timeout=5, max_retries=2, json={})

        assert result is mock_200
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2**0 = 1

    def test_retries_on_503_then_succeeds(self):
        """Retries after 503 (server error), returns response on success."""
        from src.providers.base import _post_with_retry

        mock_503 = self._make_response(503)
        mock_200 = self._make_response(200)

        with patch("src.providers.base.requests.post", side_effect=[mock_503, mock_200]), \
             patch("src.providers.base.time.sleep") as mock_sleep:
            result = _post_with_retry("http://x", timeout=5, max_retries=2)

        assert result is mock_200
        mock_sleep.assert_called_once_with(1)

    def test_exponential_backoff_sleep_values(self):
        """Sleep durations follow 2**attempt: 1s then 2s."""
        from src.providers.base import _post_with_retry

        mock_429 = self._make_response(429)
        mock_200 = self._make_response(200)

        with patch("src.providers.base.requests.post", side_effect=[mock_429, mock_429, mock_200]), \
             patch("src.providers.base.time.sleep") as mock_sleep:
            _post_with_retry("http://x", timeout=5, max_retries=2)

        assert mock_sleep.call_args_list == [call(1), call(2)]

    def test_raises_after_exhausting_all_retries_on_429(self):
        """Raises HTTPError after all attempts return 429."""
        from src.providers.base import _post_with_retry

        mock_429 = self._make_response(429)

        with patch("src.providers.base.requests.post", return_value=mock_429) as mock_post, \
             patch("src.providers.base.time.sleep"):
            with pytest.raises(req_lib.HTTPError):
                _post_with_retry("http://x", timeout=5, max_retries=2)

        assert mock_post.call_count == 3  # 1 initial + 2 retries

    def test_retries_on_timeout_then_succeeds(self):
        """Retries after Timeout exception, returns response on success."""
        from src.providers.base import _post_with_retry

        mock_200 = self._make_response(200)

        with patch("src.providers.base.requests.post",
                   side_effect=[req_lib.exceptions.Timeout, mock_200]) as mock_post, \
             patch("src.providers.base.time.sleep") as mock_sleep:
            result = _post_with_retry("http://x", timeout=5, max_retries=2)

        assert result is mock_200
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(1)

    def test_raises_timeout_after_exhausting_retries(self):
        """Raises Timeout after all attempts time out."""
        from src.providers.base import _post_with_retry

        with patch("src.providers.base.requests.post",
                   side_effect=req_lib.exceptions.Timeout) as mock_post, \
             patch("src.providers.base.time.sleep"):
            with pytest.raises(req_lib.exceptions.Timeout):
                _post_with_retry("http://x", timeout=5, max_retries=2)

        assert mock_post.call_count == 3

    def test_does_not_retry_on_401(self):
        """401 Unauthorized is not retried — retrying an auth error is pointless."""
        from src.providers.base import _post_with_retry

        mock_401 = self._make_response(401)

        with patch("src.providers.base.requests.post", return_value=mock_401) as mock_post, \
             patch("src.providers.base.time.sleep") as mock_sleep:
            with pytest.raises(req_lib.HTTPError):
                _post_with_retry("http://x", timeout=5, max_retries=2)

        assert mock_post.call_count == 1  # no retries
        mock_sleep.assert_not_called()

    def test_does_not_retry_on_400(self):
        """400 Bad Request is not retried."""
        from src.providers.base import _post_with_retry

        mock_400 = self._make_response(400)

        with patch("src.providers.base.requests.post", return_value=mock_400) as mock_post, \
             patch("src.providers.base.time.sleep") as mock_sleep:
            with pytest.raises(req_lib.HTTPError):
                _post_with_retry("http://x", timeout=5, max_retries=2)

        assert mock_post.call_count == 1
        mock_sleep.assert_not_called()

    def test_zero_retries_raises_immediately(self):
        """With max_retries=0, a single failure raises with no sleep."""
        from src.providers.base import _post_with_retry

        with patch("src.providers.base.requests.post",
                   side_effect=req_lib.exceptions.Timeout) as mock_post, \
             patch("src.providers.base.time.sleep") as mock_sleep:
            with pytest.raises(req_lib.exceptions.Timeout):
                _post_with_retry("http://x", timeout=5, max_retries=0)

        assert mock_post.call_count == 1
        mock_sleep.assert_not_called()

    def test_timeout_value_passed_to_requests(self):
        """The timeout argument is forwarded to requests.post."""
        from src.providers.base import _post_with_retry

        mock_200 = self._make_response(200)

        with patch("src.providers.base.requests.post", return_value=mock_200) as mock_post:
            _post_with_retry("http://x", timeout=42, max_retries=0)

        _, kwargs = mock_post.call_args
        assert kwargs["timeout"] == 42


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------

class TestOpenAIProvider:
    def test_stub_when_no_api_key(self, monkeypatch):
        """Returns stub string when OPENAI_API_KEY is not set."""
        monkeypatch.setenv("OPENAI_API_KEY", "")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.openai_provider as m; reload(m)

        result = m.OpenAIProvider().generate("hello")
        assert result.startswith("[openai-stub]")
        assert "hello" in result

    def test_parses_successful_response(self, monkeypatch):
        """Extracts content from OpenAI chat completion response."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.openai_provider as m; reload(m)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "RAG stands for Retrieval-Augmented Generation."}}]
        }

        with patch("src.providers.base.requests.post", return_value=mock_resp):
            result = m.OpenAIProvider().generate("What is RAG?")

        assert result == "RAG stands for Retrieval-Augmented Generation."

    def test_uses_configured_timeout(self, monkeypatch):
        """Passes LLM_TIMEOUT_SECONDS to the HTTP call."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "10")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.openai_provider as m; reload(m)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        with patch("src.providers.base.requests.post", return_value=mock_resp) as mock_post:
            m.OpenAIProvider().generate("test")

        _, kwargs = mock_post.call_args
        assert kwargs["timeout"] == 10

    def test_raises_on_auth_failure(self, monkeypatch):
        """Propagates HTTPError on 401 without retrying."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-bad")
        monkeypatch.setenv("LLM_MAX_RETRIES", "2")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.openai_provider as m; reload(m)

        mock_401 = MagicMock()
        mock_401.status_code = 401
        mock_401.raise_for_status.side_effect = req_lib.HTTPError()

        with patch("src.providers.base.requests.post", return_value=mock_401) as mock_post, \
             patch("src.providers.base.time.sleep"):
            with pytest.raises(req_lib.HTTPError):
                m.OpenAIProvider().generate("test")

        assert mock_post.call_count == 1  # no retries on 401

    def test_retries_on_rate_limit(self, monkeypatch):
        """Retries up to LLM_MAX_RETRIES times on 429."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        monkeypatch.setenv("LLM_MAX_RETRIES", "2")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.openai_provider as m; reload(m)

        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.raise_for_status.side_effect = req_lib.HTTPError()

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.raise_for_status = MagicMock()
        mock_200.json.return_value = {"choices": [{"message": {"content": "ok after retry"}}]}

        with patch("src.providers.base.requests.post", side_effect=[mock_429, mock_200]) as mock_post, \
             patch("src.providers.base.time.sleep"):
            result = m.OpenAIProvider().generate("test")

        assert result == "ok after retry"
        assert mock_post.call_count == 2


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

class TestAnthropicProvider:
    def test_stub_when_no_api_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.anthropic_provider as m; reload(m)

        result = m.AnthropicProvider().generate("hello")
        assert result.startswith("[anthropic-stub]")

    def test_parses_successful_response(self, monkeypatch):
        """Extracts text from Anthropic content block response."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.anthropic_provider as m; reload(m)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "content": [{"type": "text", "text": "The answer is 42."}]
        }

        with patch("src.providers.base.requests.post", return_value=mock_resp):
            result = m.AnthropicProvider().generate("What is the answer?")

        assert result == "The answer is 42."

    def test_retries_on_503(self, monkeypatch):
        """Retries on 503 service unavailable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        monkeypatch.setenv("LLM_MAX_RETRIES", "1")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.anthropic_provider as m; reload(m)

        mock_503 = MagicMock()
        mock_503.status_code = 503
        mock_503.raise_for_status.side_effect = req_lib.HTTPError()

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.raise_for_status = MagicMock()
        mock_200.json.return_value = {"content": [{"type": "text", "text": "recovered"}]}

        with patch("src.providers.base.requests.post", side_effect=[mock_503, mock_200]) as mock_post, \
             patch("src.providers.base.time.sleep"):
            result = m.AnthropicProvider().generate("test")

        assert result == "recovered"
        assert mock_post.call_count == 2


# ---------------------------------------------------------------------------
# Gemini provider
# ---------------------------------------------------------------------------

class TestGeminiProvider:
    def test_stub_when_no_api_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.gemini_provider as m; reload(m)

        result = m.GeminiProvider().generate("hello")
        assert result.startswith("[gemini-stub]")

    def test_parses_successful_response(self, monkeypatch):
        """Extracts text from Gemini candidates response."""
        monkeypatch.setenv("GEMINI_API_KEY", "AIza-fake")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.gemini_provider as m; reload(m)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Gemini says hello."}]}}]
        }

        with patch("src.providers.base.requests.post", return_value=mock_resp):
            result = m.GeminiProvider().generate("Say hello")

        assert result == "Gemini says hello."

    def test_raises_after_exhausting_retries(self, monkeypatch):
        """Raises Timeout after all retry attempts are exhausted."""
        monkeypatch.setenv("GEMINI_API_KEY", "AIza-fake")
        monkeypatch.setenv("LLM_MAX_RETRIES", "1")
        from importlib import reload
        import src.core.settings as s; reload(s)
        import src.providers.gemini_provider as m; reload(m)

        with patch("src.providers.base.requests.post",
                   side_effect=req_lib.exceptions.Timeout) as mock_post, \
             patch("src.providers.base.time.sleep"):
            with pytest.raises(req_lib.exceptions.Timeout):
                m.GeminiProvider().generate("test")

        assert mock_post.call_count == 2  # 1 initial + 1 retry
