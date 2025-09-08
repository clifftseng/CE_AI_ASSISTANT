import asyncio
import json
from typing import Dict, AsyncGenerator, Callable

class SseManager:
    def __init__(self):
        self._jobs: dict[str, dict[str, asyncio.Queue]] = {}

    def connect(self, job_id: str, client_id: str) -> asyncio.Queue:
        job = self._jobs.setdefault(job_id, {})
        q = asyncio.Queue()
        job[client_id] = q
        return q

    def disconnect(self, job_id: str, client_id: str):
        job = self._jobs.get(job_id, {})
        job.pop(client_id, None)
        if not job:
            self._jobs.pop(job_id, None)

    async def send_event(self, job_id: str, event_name: str, payload: dict):
        job = self._jobs.get(job_id)
        if not job:
            return
        event = {"event": event_name, "data": json.dumps(payload, ensure_ascii=False)}
        for q in job.values():
            await q.put(event)

sse_manager = SseManager()