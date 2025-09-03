import os, httpx
from typing import Literal

Task = Literal["draft","reason","classify"]

class ModelRouter:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    async def run(self, task: Task, prompt: str):
        target = self.cfg["router"].get(task, "ollama:qwen2.5:14b-instruct")
        provider, model = target.split(":", 1)
        if provider == "ollama":
            return await self._ollama(model, prompt)
        if provider == "vertex":
            return await self._vertex(model, prompt)
        raise NotImplementedError(f"Provider {provider} not configured")

    async def _ollama(self, model: str, prompt: str):
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{self.ollama_url}/api/generate", json={"model": model, "prompt": prompt})
            r.raise_for_status()
            return r.json().get("response", "")

    async def _vertex(self, model: str, prompt: str):
        # Placeholder: call a gateway you control, or use google-genai client if running on GCP.
        # For local dev, mock the response to keep flows testable.
        return f"[vertex:{model}] " + prompt[:200]