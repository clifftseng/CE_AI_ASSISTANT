import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_sse_stream_receives_progress_event():
    from app.routers.alt import alt_service
    from pathlib import Path
    
    job_id = "test-sse-job-123"
    fake_file_path = Path("/tmp/fake_test_file.xlsx")
    alt_service.register_job(job_id, fake_file_path)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/alt/stream/{job_id}", timeout=10)
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        found_progress_event = False
        try:
            async for line in response.aiter_lines():
                if line.startswith("event: progress"):
                    found_progress_event = True
                    break
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for SSE 'progress' event.")
        except Exception as e:
            pytest.fail(f"An error occurred while reading SSE stream: {e}")

        assert found_progress_event, "Did not receive a 'progress' event from the SSE stream."
