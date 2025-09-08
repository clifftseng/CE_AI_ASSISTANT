import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings
from app.core.storage import storage_service
from app.services.alt_service import AltService
from app.models.schemas import JobResponse
from app.utils.file_validation import validate_file

router = APIRouter()
alt_service = AltService()

@router.post("/upload", response_model=JobResponse)
async def upload_for_alt_search(file: UploadFile = File(...)):
    allowed_excel_exts = [ext.strip() for ext in settings.ALLOWED_EXCEL_EXTS.split(',')]
    validate_file(file, allowed_excel_exts, settings.MAX_FILE_SIZE_MB)
    
    saved_path = await storage_service.save_upload(file)
    
    job_id = str(uuid.uuid4())
    alt_service.register_job(job_id, saved_path)
    
    return {"job_id": job_id}

@router.get("/stream/{job_id}")
async def stream_alt_search_results(request: Request, job_id: str):
    file_path = alt_service.get_job_filepath(job_id)
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    event_generator = alt_service.process_file(request, file_path)
    return EventSourceResponse(event_generator)
