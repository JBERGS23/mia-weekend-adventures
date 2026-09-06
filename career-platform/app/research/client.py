"""The research layer: live web research with structured results.

Everything in this app that needs current information from the internet -
scanning job boards, refreshing academy links, checking what senior AI roles
actually ask for, finding networking angles - goes through this one module.

How it works: the Anthropic API is called with the server-side web search tool
enabled, so Claude runs the searches on Anthropic's infrastructure and reads
the results, then returns an answer constrained to a JSON schema we supply. No
scraper API, no browser automation, no per-site parsers to maintain - which is
what makes the wide sourcing in spec 1.4 practical.

Two design rules the rest of the app relies on:

1. **This layer is optional.** With no API key the app still runs: browsing,
   the daily quiz on the built-in primers, shortlisting, the archive and the
   networking review all work offline. Only live scanning and content refresh
   need a key, and they say so plainly rather than failing obscurely.
2. **This layer never touches the database schema of other modules.** It
   returns plain Python dicts. Callers decide what to store.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import config
from app import db

logger = logging.getLogger(__name__)

# The server-side web search tool. Claude runs the searches itself and reads
# the results within the same API call.
WEB_SEARCH_TOOL_TYPE = "web_search_20260209"


class ResearchUnavailable(RuntimeError):
    """Raised when a research call is attempted with no API key configured."""


@dataclass
class ResearchResult:
    """What a research call returns.

    `data` is the parsed JSON matching the schema that was requested. `ok` is
    False when the call failed; callers should degrade rather than crash, since
    one dead source should never abort a whole scan.
    """

    ok: bool
    data: Any = None
    error: Optional[str] = None
    searches: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    citations: list[dict] = field(default_factory=list)

    @property
    def items(self) -> list[dict]:
        """Convenience for the common case of a schema wrapping a list."""
        if isinstance(self.data, dict):
            for value in self.data.values():
                if isinstance(value, list):
                    return value
        if isinstance(self.data, list):
            return self.data
        return []


class ResearchClient:
    """Thin wrapper over the Anthropic Messages API with web search."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else config.ANTHROPIC_API_KEY
        self.model = model or config.RESEARCH_MODEL
        self._client = None

    @property
    def available(self) -> bool:
        """True when live research can actually run."""
        if not self.api_key:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=config.RESEARCH_TIMEOUT,
                max_retries=3,
            )
        return self._client

    # -----------------------------------------------------------------
    # The one method everything else calls
    # -----------------------------------------------------------------

    def research(
        self,
        *,
        purpose: str,
        system: str,
        prompt: str,
        schema: dict,
        max_searches: Optional[int] = None,
        allowed_domains: Optional[list[str]] = None,
        use_search: bool = True,
        effort: Optional[str] = None,
    ) -> ResearchResult:
        """Run one research task and return JSON matching `schema`.

        `purpose` is a short label used for the call log, e.g. "scan:aijobs".
        `schema` must be a JSON Schema object with `additionalProperties: false`
        and a `required` list, which is what makes the response parse reliably.
        """
        if not self.available:
            return ResearchResult(
                ok=False,
                error=(
                    "No ANTHROPIC_API_KEY set, so live research is switched off. "
                    "Everything else in the app still works."
                ),
            )

        started = time.time()
        try:
            data, meta = self._call(
                system=system,
                prompt=prompt,
                schema=schema,
                max_searches=max_searches,
                allowed_domains=allowed_domains,
                use_search=use_search,
                effort=effort,
            )
        except Exception as exc:  # noqa: BLE001 - one bad source must not kill a scan
            duration = int((time.time() - started) * 1000)
            message = self._describe_error(exc)
            logger.warning("Research call %s failed: %s", purpose, message)
            self._log_call(purpose, ok=False, error=message, duration_ms=duration)
            return ResearchResult(ok=False, error=message, duration_ms=duration)

        duration = int((time.time() - started) * 1000)
        result = ResearchResult(
            ok=True,
            data=data,
            searches=meta["searches"],
            input_tokens=meta["input_tokens"],
            output_tokens=meta["output_tokens"],
            duration_ms=duration,
            citations=meta["citations"],
        )
        self._log_call(
            purpose,
            ok=True,
            duration_ms=duration,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            searches=result.searches,
        )
        return result

    # -----------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------

    def _call(
        self,
        *,
        system: str,
        prompt: str,
        schema: dict,
        max_searches: Optional[int],
        allowed_domains: Optional[list[str]],
        use_search: bool,
        effort: Optional[str],
    ) -> tuple[Any, dict]:
        client = self._get_client()

        tools: list[dict] = []
        if use_search:
            tool: dict[str, Any] = {
                "type": WEB_SEARCH_TOOL_TYPE,
                "name": "web_search",
                "max_uses": max_searches or config.MAX_SEARCHES_PER_SOURCE,
            }
            if allowed_domains:
                tool["allowed_domains"] = allowed_domains
            tools.append(tool)

        request: dict[str, Any] = {
            "model": self.model,
            # Streaming, because these calls are long and the output can be
            # large; get_final_message() reassembles it for us.
            "max_tokens": 32000,
            "system": system,
            "thinking": {"type": "adaptive"},
            "output_config": {
                "effort": effort or config.RESEARCH_EFFORT,
                "format": {"type": "json_schema", "schema": schema},
            },
            "messages": [{"role": "user", "content": prompt}],
        }
        if tools:
            request["tools"] = tools

        response = self._stream(client, request)

        # A server-tool loop can pause after its internal iteration limit.
        # Resuming is just re-sending the conversation; the API picks up where
        # it left off, and we must not inject a "continue" message.
        messages = list(request["messages"])
        resumes = 0
        while response.stop_reason == "pause_turn" and resumes < config.MAX_PAUSE_RESUMES:
            messages = messages + [{"role": "assistant", "content": response.content}]
            resumed_request = dict(request, messages=messages)
            response = self._stream(client, resumed_request)
            resumes += 1

        if response.stop_reason == "refusal":
            detail = ""
            if getattr(response, "stop_details", None):
                detail = f" ({response.stop_details.category})"
            raise RuntimeError(f"The model declined this research request{detail}.")

        text = self._extract_text(response)
        if not text:
            raise RuntimeError("The model returned no text to parse.")

        data = self._parse_json(text)

        meta = {
            "searches": self._count_searches(response),
            "input_tokens": getattr(response.usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(response.usage, "output_tokens", 0) or 0,
            "citations": self._collect_citations(response),
        }
        return data, meta

    @staticmethod
    def _stream(client, request: dict):
        """Send one request. Streaming avoids HTTP timeouts on long searches."""
        with client.messages.stream(**request) as stream:
            return stream.get_final_message()

    @staticmethod
    def _extract_text(response) -> str:
        """Join the text blocks. With a JSON schema set, this is the JSON."""
        parts = [block.text for block in response.content if block.type == "text"]
        return "\n".join(part for part in parts if part).strip()

    @staticmethod
    def _parse_json(text: str) -> Any:
        """Parse the response, tolerating a stray code fence."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3]
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            start, end = cleaned.find("["), cleaned.rfind("]")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Response was not valid JSON.")
        return json.loads(cleaned[start : end + 1])

    @staticmethod
    def _count_searches(response) -> int:
        count = 0
        for block in response.content:
            if getattr(block, "type", "") == "server_tool_use":
                if getattr(block, "name", "") == "web_search":
                    count += 1
        return count

    @staticmethod
    def _collect_citations(response) -> list[dict]:
        """Pull out the pages the model actually read, for provenance."""
        found: list[dict] = []
        seen: set[str] = set()
        for block in response.content:
            if getattr(block, "type", "") != "web_search_tool_result":
                continue
            content = getattr(block, "content", None)
            # On error the content is a single object rather than a list.
            if not isinstance(content, list):
                continue
            for result in content:
                url = getattr(result, "url", None)
                if url and url not in seen:
                    seen.add(url)
                    found.append({"url": url, "title": getattr(result, "title", "") or ""})
        return found

    @staticmethod
    def _describe_error(exc: Exception) -> str:
        """Turn an SDK exception into something readable in the UI."""
        try:
            import anthropic
        except ImportError:
            return str(exc)

        if isinstance(exc, anthropic.AuthenticationError):
            return "The Anthropic API key was rejected. Check ANTHROPIC_API_KEY."
        if isinstance(exc, anthropic.PermissionDeniedError):
            return "The API key lacks permission for this request."
        if isinstance(exc, anthropic.RateLimitError):
            return "Rate limited by the Anthropic API. Try again shortly."
        if isinstance(exc, anthropic.APITimeoutError):
            return "The research call timed out. This source may be slow; try again."
        if isinstance(exc, anthropic.APIConnectionError):
            return "Could not reach the Anthropic API. Check the network connection."
        if isinstance(exc, anthropic.APIStatusError):
            if exc.status_code >= 500:
                return f"Anthropic API server error ({exc.status_code}). Try again later."
            return f"API error ({exc.status_code}): {exc.message}"
        return f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _log_call(
        purpose: str,
        *,
        ok: bool,
        duration_ms: int,
        error: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        searches: int = 0,
    ) -> None:
        """Record the call so cost and failures are visible in the UI."""
        try:
            with db.session() as conn:
                db.insert(
                    conn,
                    "research_calls",
                    {
                        "purpose": purpose,
                        "model": config.RESEARCH_MODEL,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "web_searches": searches,
                        "duration_ms": duration_ms,
                        "ok": 1 if ok else 0,
                        "error": error,
                        "created_at": db.utcnow(),
                    },
                )
        except Exception:  # noqa: BLE001 - logging must never break a scan
            logger.exception("Could not write research call log")


# A single shared instance is enough for a single-user local app.
_default_client: Optional[ResearchClient] = None


def get_client() -> ResearchClient:
    global _default_client
    if _default_client is None:
        _default_client = ResearchClient()
    return _default_client
