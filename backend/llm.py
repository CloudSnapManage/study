"""OpenAI-compatible streaming client with deterministic local fallback."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from .config import Settings
from .tools import search_course_materials


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_chat(settings: Settings, message: str, mode: str = "agent") -> AsyncIterator[str]:
    results = search_course_materials(settings, message)
    yield sse("tool_start", {"name": "search_course_materials", "arguments": {"query": message}})
    yield sse("tool_result", {"name": "search_course_materials", "count": len(results), "results": results[:4]})
    profile = None
    from .database import connect_db
    with connect_db(settings) as db:
        profile = db.execute("SELECT * FROM llm_profiles WHERE role='chat' ORDER BY is_fallback DESC,id LIMIT 1").fetchone()
    if profile:
        headers = {"Authorization": f"Bearer {profile['api_key'] or 'ollama'}"}
        payload = {"model": profile["model_id"], "messages": [{"role": "user", "content": message}], "stream": True}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3, read=30)) as client:
                async with client.stream("POST", f"{profile['base_url'].rstrip('/')}/chat/completions", headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        parsed = json.loads(data)
                        token = parsed.get("choices", [{}])[0].get("delta", {}).get("content")
                        if token:
                            yield sse("token", {"text": token})
                    yield sse("done", {"fallback": False})
                    return
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError):
            pass
    if results:
        summary = "\n\n".join(item["content"][:600] for item in results[:3])
        for item in results[:3]:
            yield sse("citation", {"document_id": item["document_id"], "filename": item["filename"], "page_number": item["page_number"]})
        text = f"Local retrieval result:\n\n{summary}"
    else:
        text = "No indexed course material matched this request. Scan PDFs in ./materials/notes or ./materials/past_papers."
    yield sse("token", {"text": text})
    yield sse("done", {"fallback": True})
