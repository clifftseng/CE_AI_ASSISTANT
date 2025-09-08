import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from typing import List
import asyncio, logging
import os

from app.core.config import settings
from app.core.storage import storage_service
from app.services.value_service import process_files, job_statuses
from app.models.schemas import JobResponse, ValueResultResponse
from app.utils.file_validation import validate_files

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload_polling", response_model=JobResponse)
async def upload_for_value_search_polling(
    background_tasks: BackgroundTasks,
    excel: UploadFile = File(...),
    pdfs: List[UploadFile] = File(...)
):
    validate_files([excel] + pdfs, settings)

    job_id = str(uuid.uuid4())
    logger.info(f"[upload_polling] job_id=%s accepting files", job_id)
    logger.info("[upload_polling] pid=%s", os.getpid())
    
    saved_excel_path = await storage_service.save_upload(excel)
    saved_pdf_paths = [await storage_service.save_upload(f) for f in pdfs]

    asyncio.create_task(process_files(job_id, [saved_excel_path], saved_pdf_paths, job_type="polling"))
    logger.info(f"[upload_polling] job_id=%s scheduled process_files", job_id)
    
    return {"job_id": job_id}

@router.get("/result_polling/{job_id}", response_model=ValueResultResponse)
async def get_value_search_result_polling(job_id: str):
    result = job_statuses.get(job_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return result
