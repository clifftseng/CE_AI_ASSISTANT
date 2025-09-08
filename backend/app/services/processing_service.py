import asyncio
from pathlib import Path
from typing import List, Dict, Any
# import pandas as pd # Not directly used here anymore
# from uuid import uuid4 # Not directly used here anymore

from app.core.config import settings # Still needed for DATA_DIR if used for temp files
from app.utils.sse import sse_manager # Import sse_manager for status updates
from app.core.job_manager import job_statuses # Import job_statuses from the new job_manager module

# Imports from aoai_method
from aoai_method.document_intelligence import analyze_pdf
from aoai_method.processing_module import create_structured_document

# Placeholder for Azure/AOAI related imports if they were present
# from app.services.azure_service import AzureService
# from app.services.excel_service import ExcelService

async def process_documents(
    job_id: str, pdf_paths: List[Path], job_type: str
) -> List[Dict[str, Any]]:
    """
    Processes uploaded PDF documents using Azure Document Intelligence and returns structured data.
    """
    all_structured_docs: List[Dict[str, Any]] = []

    for i, pdf_path in enumerate(pdf_paths):
        message = f"正在處理 PDF 文件 ({i+1}/{len(pdf_paths)}): {pdf_path.name}"
        print(f"[{job_id}] {message}")
        if job_type == "polling":
            job_statuses[job_id]["message"] = message
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "status", {"message": message, "status": "processing"})

        try:
            # 1. Analyze PDF with Document Intelligence
            di_data = analyze_pdf(str(pdf_path))
            
            if not di_data:
                print(f"[{job_id}] [WARNING] Document Intelligence returned no data for {pdf_path.name}. Skipping.")
                if job_type == "polling":
                    job_statuses[job_id]["message"] = f"警告: {pdf_path.name} 未獲取到數據，跳過。"
                elif job_type == "sse":
                    await sse_manager.send_event(job_id, "status", {"message": f"警告: {pdf_path.name} 未獲取到數據，跳過。", "status": "processing"})
                continue

            # 2. Structure PDF content
            structured_document = create_structured_document(di_data)
            
            all_structured_docs.append({
                "id": pdf_path.stem, # Use stem as ID
                "title": pdf_path.name,
                "ocr_json": structured_document
            })

        except Exception as e:
            error_msg = f"處理 {pdf_path.name} 失敗: {e}"
            print(f"[{job_id}] [ERROR] {error_msg}")
            if job_type == "polling":
                job_statuses[job_id]["message"] = f"錯誤: {error_msg}"
            elif job_type == "sse":
                await sse_manager.send_event(job_id, "status", {"message": f"錯誤: {error_msg}", "status": "processing"})
            # Continue to process other PDFs even if one fails

    return all_structured_docs