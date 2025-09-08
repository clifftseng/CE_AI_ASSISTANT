# backend/app/services/aoai_processing_service.py
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Callable, Awaitable

from app.core.job_manager import get_job_dirs
from app.services.excel_processing_service import get_excel_query_data, write_summary_to_excel
from app.services.azure_di_service import analyze_pdf
from app.services.di_processing_service import create_structured_document
from app.services.aoai_core_service import build_user_payload, call_aoai_extractor

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Define a type for the async callback
StatusCallback = Callable[[str], Awaitable[None]]

async def _run_di_on_all_pdfs(
    pdf_paths: List[Path], 
    di_output_dir: Path,
    update_status: StatusCallback
) -> None: 
    """Runs Document Intelligence on all PDF files and saves the raw JSON output."""
    
    async def process_single_pdf(pdf_path: Path, index: int):
        try:
            await update_status(f"正在處理 PDF 文件 ({index}/{len(pdf_paths)}): {pdf_path.name}...")
            di_result = await analyze_pdf(pdf_path)
            output_path = di_output_dir / f"{pdf_path.stem}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(di_result, f, ensure_ascii=False, indent=2)
            print(f"  - DI result for {pdf_path.name} saved to {output_path}")
        except Exception as e:
            print(f"[ERROR] Failed DI analysis for {pdf_path.name}: {e}")
            # Optionally, report a non-fatal error for this specific file
            await update_status(f"處理 PDF 文件 {pdf_path.name} 失敗: {e}")


    di_output_dir.mkdir(parents=True, exist_ok=True)
    tasks = [process_single_pdf(path, i + 1) for i, path in enumerate(pdf_paths)]
    await asyncio.gather(*tasks)

def _load_and_structure_di_results(di_output_dir: Path) -> List[Dict[str, Any]]:
    """Loads raw DI JSONs and converts them to the structured format for AOAI."""
    structured_docs = []
    print(f"\nLoading and structuring DI results from '{di_output_dir}'...")
    
    for json_path in di_output_dir.glob("*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                raw_di_data = json.load(f)
            
            structured_data = create_structured_document(raw_di_data)
            
            structured_docs.append({
                "id": json_path.stem,
                "title": json_path.name,
                "ocr_json": structured_data
            })
            print(f"  - Loaded and structured: {json_path.name}")
        except Exception as e:
            print(f"[WARNING] Could not load or structure {json_path.name}: {e}")
            
    return structured_docs

async def process_aoai_job(
    job_id: str, 
    pdf_paths: List[Path], 
    excel_path: Path,
    update_status: StatusCallback
) -> Path:
    """
    Main orchestrator for the AOAI extraction process with status updates.
    """
    print(f"--- Starting AOAI Job --- (ID: {job_id})")
    job_dirs = get_job_dirs(job_id)

    await update_status("讀取 Excel 設定...")
    query_data = await get_excel_query_data(excel_path)
    print(f"  - Query Targets (PNs): {query_data.query_targets}")
    print(f"  - Query Fields (Items): {query_data.query_fields}")

    di_output_dir = job_dirs.di_results
    await _run_di_on_all_pdfs(pdf_paths, di_output_dir, update_status)

    await update_status("轉換文件結構中...")
    structured_docs = _load_and_structure_di_results(di_output_dir)
    if not structured_docs:
        raise ValueError("No DI results could be processed. Aborting job.")

    await update_status("載入 AI 模型提示...")
    try:
        system_prompt_path = PROMPTS_DIR / "SYSTEM_PROMPT.json"
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"System prompt not found at {system_prompt_path}")

    await update_status("建構 AI 請求...")
    user_payload = build_user_payload(
        docs=structured_docs,
        pns=query_data.query_targets,
        items=query_data.query_fields
    )
    
    await update_status("呼叫 Azure OpenAI 進行數據抽取...")
    aoai_result = await call_aoai_extractor(system_prompt, user_payload)
    if "error" in aoai_result:
        raise ValueError(f"AOAI extraction failed: {aoai_result['error']}")

    await update_status("正在產生最終報告...")
    output_dir = job_dirs.output
    summary_file_path = await write_summary_to_excel(
        original_excel_path=excel_path,
        query_data=query_data,
        aoai_result=aoai_result,
        output_dir=output_dir
    )

    print(f"\n--- Job {job_id} Completed Successfully ---")
    return summary_file_path
