# backend/app/services/value_service.py
import logging
from pathlib import Path
from typing import List
import traceback

from app.core.job_manager import job_statuses
from app.core.storage import storage_service
from app.services.aoai_processing_service import process_aoai_job

logger = logging.getLogger(__name__)

async def process_files(job_id: str, excel_paths: List[Path], pdf_paths: List[Path], job_type: str) -> None:
    """
    Orchestrates the file processing job, updating status via polling or SSE.
    """
    
    async def update_status(message: str):
        """Helper to send status updates based on job type."""
        logger.info(f"[{job_id}] Status: {message}")
        if job_type == "polling":
            job_statuses[job_id] = {"status": "processing", "message": message, "download_url": None, "query_fields": None, "query_targets": None}

    try:
        logger.info(f"[process_files] Start job_id={job_id}, job_type={job_type}")
        await update_status("已接受工作，開始處理…")

        # --- 1. Validate Input Files ---
        if len(excel_paths) != 1:
            raise ValueError(f"預期應有 1 個 Excel 檔案，但收到了 {len(excel_paths)} 個。")
        excel_path = excel_paths[0]

        if not pdf_paths:
            raise ValueError("至少需要提供 1 個 PDF 檔案。")

        # --- 2. Call the Core Processing Service ---
        # The core service will handle all steps and use the callback to report progress.
        final_excel_path = await process_aoai_job(
            job_id=job_id,
            pdf_paths=pdf_paths,
            excel_path=excel_path,
            update_status=update_status
        )

        # --- 3. Finalize Job ---
        download_url = storage_service.make_downloadable(final_excel_path)
        final_result = {
            "message": "處理完成",
            "status": "done",
            "download_url": download_url,
        }

        if job_type == "polling":
            job_statuses[job_id] = final_result
        
        logger.info(f"[process_files] Done job_id={job_id}")

    except Exception as e:
        logger.exception(f"[process_files] Fail job_id={job_id} err={e}")
        error_message = {"message": f"處理失敗：{e}", "status": "error", "details": traceback.format_exc()}
        
        if job_type == "polling":
            job_statuses[job_id] = error_message
