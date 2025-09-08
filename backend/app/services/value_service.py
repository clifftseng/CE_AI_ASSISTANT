import asyncio, traceback
from pathlib import Path
from typing import List, Dict, Any
from app.utils.sse import sse_manager
from app.core.storage import storage_service
from app.core.config import settings
import logging, uuid
import os
import json # Needed for JSON schema and payload

from app.services.processing_service import process_documents # Now returns structured PDF data
from app.services.excel_service import get_excel_query_data_from_path # Still needed for initial Excel read
from app.services.aoai_processing_service import build_user_payload, call_aoai_extractor, write_summary_to_excel # New imports for AOAI orchestration

# Imports from aoai_method for schema and prompt reading
from aoai_method.aoai_service import read_prompt_core, load_schema

# Import job_statuses from the new job_manager module
from app.core.job_manager import job_statuses

logger = logging.getLogger(__name__)

async def process_files(job_id: str, excel_paths: List[Path], pdf_paths: List[Path], job_type: str) -> None:
    try:
        logger.info("[process_files] start job_id=%s, job_type=%s", job_id, job_type)
        logger.info("[process_files] pid=%s", os.getpid())

        if job_type == "polling":
            job_statuses[job_id] = {"status": "processing", "message": "已接受工作，開始處理…"}
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "status", {"message": "已接受工作，開始處理…", "status": "processing"})
            logger.info(f"[{job_id}] SSE event: 已接受工作，開始處理…")
        await asyncio.sleep(1)

        # --- 1. Excel File Reading and Query Data Extraction ---
        if job_type == "polling":
            job_statuses[job_id] = {"status": "processing", "message": "讀取 Excel 設定..."}
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "status", {"message": "讀取 Excel 設定...", "status": "processing"})
            logger.info(f"[{job_id}] SSE event: 讀取 Excel 設定...")
        
        original_excel_path = excel_paths[0] # Assuming only one Excel file
        query_data = get_excel_query_data_from_path(original_excel_path)
        target_pns = query_data.get("query_targets", [])
        target_items = query_data.get("query_fields", [])
        
        logger.info(f"[{job_id}] Query Targets (PNs): {target_pns}")
        logger.info(f"[{job_id}] Query Fields (Items): {target_items}")

        # --- 2. PDF Processing (Document Intelligence) ---
        if job_type == "polling":
            job_statuses[job_id] = {"status": "processing", "message": "正在處理 PDF 文件 (Document Intelligence)..."}
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "status", {"message": "正在處理 PDF 文件 (Document Intelligence)...", "status": "processing"})
            logger.info(f"[{job_id}] SSE event: 正在處理 PDF 文件 (Document Intelligence)...")
        
        # process_documents now returns structured PDF data (docs list)
        structured_pdf_docs = await process_documents(job_id, pdf_paths, job_type) # Pass job_type
        
        if not structured_pdf_docs:
            raise ValueError("未從 PDF 文件中獲取到任何結構化數據。")

        # --- 3. Load System Prompt and Schema ---
        if job_type == "polling":
            job_statuses[job_id] = {"status": "processing", "message": "載入 AOAI 提示與 Schema..."}
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "status", {"message": "載入 AOAI 提示與 Schema...", "status": "processing"})
            logger.info(f"[{job_id}] SSE event: 載入 AOAI 提示與 Schema...")

        system_prompt_path = Path(__file__).parent.parent.parent / "aoai_method" / "schema" / "SYSTEM_PROMPT.json"
        schema_path = Path(__file__).parent.parent.parent / "aoai_method" / "schema" / "spec_tables.v2.json"

        system_prompt_content = read_prompt_core(str(system_prompt_path))
        json_schema = load_schema(str(schema_path))
        
        logger.info(f"[{job_id}] System Prompt and Schema loaded.")

        # --- 4. Build User Payload ---
        if job_type == "polling":
            job_statuses[job_id] = {"status": "processing", "message": "建構 AOAI 請求 Payload..."}
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "status", {"message": "建構 AOAI 請求 Payload...", "status": "processing"})
            logger.info(f"[{job_id}] SSE event: 建構 AOAI 請求 Payload...")

        user_payload = build_user_payload(
            docs=structured_pdf_docs,
            pns=target_pns,
            items=target_items
        )
        logger.info(f"[{job_id}] User Payload built.")

        # --- 5. Call AOAI Extractor ---
        if job_type == "polling":
            job_statuses[job_id] = {"status": "processing", "message": "呼叫 Azure OpenAI 進行數據抽取..."}
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "status", {"message": "呼叫 Azure OpenAI 進行數據抽取...", "status": "processing"})
            logger.info(f"[{job_id}] SSE event: 呼叫 Azure OpenAI 進行數據抽取...")

        aoai_result = await call_aoai_extractor(system_prompt_content, user_payload)
        
        if aoai_result.get("error"):
            raise ValueError(f"AOAI 抽取失敗: {aoai_result['error']}")
        
        logger.info(f"[{job_id}] AOAI Extraction complete.")

        # --- 6. Write Results to Excel ---
        if job_type == "polling":
            job_statuses[job_id] = {"status": "processing", "message": "將結果寫入 Excel 檔案..."}
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "status", {"message": "將結果寫入 Excel 檔案...", "status": "processing"})
            logger.info(f"[{job_id}] SSE event: 將結果寫入 Excel 檔案...")
        
        # Use the output directory from settings
        output_dir = Path(settings.DATA_DIR)
        final_excel_path = write_summary_to_excel(original_excel_path, query_data, aoai_result, output_dir)
        
        download_url = storage_service.make_downloadable(final_excel_path)
        
        final_result = {
            "message": "處理完成",
            "status": "done",
            "download_url": download_url,
            "query_fields": target_items, # Use target_items as query_fields
            "query_targets": target_pns, # Use target_pns as query_targets
        }

        if job_type == "polling":
            job_statuses[job_id] = final_result
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            await sse_manager.send_event(job_id, "result", final_result)
            logger.info(f"[{job_id}] SSE event: 處理完成")
        logger.info("[process_files] done job_id=%s", job_id)
    except Exception as e:
        logger.exception("[process_files] fail job_id=%s err=%s", job_id, e)
        error_message = {"message": f"處理失敗：{e}", "status": "error"}
        if job_type == "polling":
            job_statuses[job_id] = error_message
            logger.info(f"[{job_id}] Status update: {job_statuses[job_id]['message']}")
        elif job_type == "sse":
            try:
                await sse_manager.send_event(job_id, "error", error_message)
                logger.info(f"[{job_id}] SSE event: 錯誤 - {error_message['message']}")
            except Exception:
                pass
