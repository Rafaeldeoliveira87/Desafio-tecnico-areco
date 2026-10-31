import asyncio
from types import SimpleNamespace

import httpx
import pytest

import app.llm.factory as factory
from app.core.exceptions import ProviderError
from app.llm.openai_compatible import OpenAICompatibleProvider
from app.models.schemas import Category
from app.services.classifier import Orchestrator


class FakeResponse:
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://provider.test/chat")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("provider failure", request=request, response=response)

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


class FakeAsyncClient:
    response = FakeResponse("resposta fundamentada")
    calls = 0

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, *args, **kwargs):
        type(self).calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def provider(retries=0):
    return OpenAICompatibleProvider(
        endpoint="https://provider.test/chat",
        api_key="test-key-not-a-credential",
        model="fake-model",
        timeout=0.1,
        max_retries=retries,
    )


def test_provider_success_uses_returned_content(monkeypatch):
    FakeAsyncClient.response = FakeResponse("resposta fundamentada")
    FakeAsyncClient.calls = 0
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    result = asyncio.run(provider().generate("system", "question"))
    assert result == "resposta fundamentada"
    assert FakeAsyncClient.calls == 1


def test_invalid_provider_json_falls_back_to_local_classifier(monkeypatch):
    FakeAsyncClient.response = FakeResponse("isso não é JSON")
    FakeAsyncClient.calls = 0
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    result = asyncio.run(Orchestrator(provider()).classify("Como solicito férias?"))
    assert result.category == Category.INFORMACOES_INTERNAS


def test_provider_timeout_retries_and_returns_safe_error(monkeypatch):
    FakeAsyncClient.response = httpx.ReadTimeout("private timeout detail")
    FakeAsyncClient.calls = 0
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    with pytest.raises(ProviderError) as error:
        asyncio.run(provider(retries=1).generate("system", "question"))
    assert FakeAsyncClient.calls == 2
    assert "private timeout detail" not in str(error.value)


def test_factory_stays_disabled_without_explicit_opt_in(monkeypatch):
    monkeypatch.setattr(
        factory,
        "settings",
        SimpleNamespace(external_processing_enabled=False, llm_provider="openai_compatible"),
    )
    assert factory.get_provider() is None


def test_factory_missing_credentials_uses_fallback(monkeypatch):
    monkeypatch.setattr(
        factory,
        "settings",
        SimpleNamespace(external_processing_enabled=True, llm_provider="openai_compatible"),
    )
    assert factory.get_provider() is None


def test_provider_rejects_plain_http_outside_loopback():
    with pytest.raises(ProviderError, match="HTTPS"):
        OpenAICompatibleProvider(
            endpoint="http://provider.example/chat",
            api_key="test-key-not-a-credential",
            model="fake-model",
        )
