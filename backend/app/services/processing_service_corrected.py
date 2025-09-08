import json
import os
import re # Import re module
from typing import List, Dict, Any

from app.services.azure_service import analyze_document_from_path, get_aoai_response
from app.services.excel_service import get_excel_query_data_from_path, create_excel_output
from app.utils.sse import sse_manager # Import sse_manager

# --- Helper functions from processing_module.py ---

def _structure_di_tables(di_tables: list) -> list:
    # (This function is adapted from aoai_method/processing_module.py)
    structured_tables = []
    if not di_tables:
        return []

    for i, table in enumerate(di_tables):
        page_number = "N/A"
        if table.get("bounding_regions"):
            page_number = table["bounding_regions"][0].get("page_number", "N/A")

        table_object = {
            "table_number": i + 1,
            "page_number": page_number,
            "rows": []
        }

        rows_dict = {}
        max_cols = 0
        for cell in table.get("cells", []):
            row_idx = cell["row_index"]
            col_idx = cell["column_index"]
            content = cell.get("content", "")
            if row_idx not in rows_dict:
                rows_dict[row_idx] = {}
            rows_dict[row_idx][col_idx] = content
            if col_idx > max_cols:
                max_cols = col_idx

        for r_idx in sorted(rows_dict.keys()):
            row_list = []
            for c_idx in range(max_cols + 1):
                row_list.append(rows_dict[r_idx].get(c_idx, ""))
            table_object["rows"].append(row_list)
        
        structured_tables.append(table_object)
        
    return structured_tables

def _create_structured_document(di_data: dict) -> dict:
    # (This function is adapted from aoai_method/processing_module.py)
    structured_tables = _structure_di_tables(di_data.get("tables", []))
    # For simplicity, we'll just pass the raw content for now.
    # The original implementation had more complex text extraction logic.
    return {
        "content": di_data.get("content", ""),
        "tables": structured_tables
    }

# --- Main Orchestration Service ---

async def process_documents(job_id: str, excel_path: str, pdf_paths: List[str]) -> bytes:
    """
    Orchestrates the entire document processing workflow.
    """
    await sse_manager.send_event(job_id, "status", {"message": "開始讀取 Excel 檔案...", "status": "processing"})
    # 1. Read original excel content to be used later for output generation
    with open(excel_path, "rb") as f:
        original_excel_content = f.read()

    await sse_manager.send_event(job_id, "status", {"message": "正在解析 Excel 查詢設定...", "status": "processing"})
    # 2. Get query data from the Excel file
    query_data = get_excel_query_data_from_path(excel_path)

    await sse_manager.send_event(job_id, "status", {"message": f"找到 {len(pdf_paths)} 個 PDF 檔案，開始處理...", "status": "processing"})
    # 3. Process all PDF files with Document Intelligence
    docs_for_aoai = []
    for i, pdf_path in enumerate(pdf_paths):
        await sse_manager.send_event(job_id, "status", {"message": f"正在分析 PDF 檔案 {i+1}/{len(pdf_paths)}: {os.path.basename(pdf_path)} (DI 處理中)...", "status": "processing"})
        di_result = analyze_document_from_path(pdf_path)
        structured_doc = _create_structured_document(di_result)
        docs_for_aoai.append({
            "id": os.path.basename(pdf_path),
            "title": os.path.basename(pdf_path),
            "ocr_json": json.dumps(structured_doc) # Embed structured JSON as a string
        })
    await sse_manager.send_event(job_id, "status", {"message": "所有 PDF 檔案分析完成，準備呼叫 AOAI...", "status": "processing"})

    # 4. Load prompts
    prompt_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
    with open(os.path.join(prompt_dir, "SYSTEM_PROMPT.json"), "r", encoding="utf-8") as f:
        system_prompt = f.read()
    with open(os.path.join(prompt_dir, "USER_PROMPT.json"), "r", encoding="utf-8") as f:
        user_prompt_template = f.read()

    # 5. Prepare user prompt with dynamic data using REGEX
    # This is a more robust way to handle multi-line, complex replacements.

    # Replace docs array
    docs_json_string = ", ".join([json.dumps(doc, ensure_ascii=False) for doc in docs_for_aoai])
    user_prompt = re.sub(r'("docs":\s*\[)[\s\S]*?(\])', f'\\1{docs_json_string}\\2', user_prompt_template, flags=re.DOTALL)

    # Replace pns array
    pns_json_string = ", ".join([f'"{pn}"' for pn in query_data["query_targets"]])
    user_prompt = re.sub(r'("pns":\s*\[)[\s\S]*?(\])', f'\\1{pns_json_string}\\2', user_prompt, flags=re.DOTALL)

    # Replace items array
    items_json_string = ", ".join([f'"{item}"' for item in query_data["query_fields"]])
    user_prompt = re.sub(r'("items":\s*\[)[\s\S]*?(\])', f'\\1{items_json_string}\\2', user_prompt, flags=re.DOTALL)

    # Replace simple options
    user_prompt = re.sub(r'"options":\s*\{[\s\S]*?\}', '"options": { "language": "zh-TW", "return_source_excerpt": false }', user_prompt, flags=re.DOTALL)
    user_prompt = re.sub(r'"excel_context":\s*\{[\s\S]*?\}', '"excel_context": null', user_prompt, flags=re.DOTALL)

    await sse_manager.send_event(job_id, "status", {"message": "正在呼叫 Azure OpenAI 服務...", "status": "processing"})
    # 6. Call AOAI
    aoai_result = get_aoai_response(system_prompt, user_prompt)

    await sse_manager.send_event(job_id, "status", {"message": "AOAI 處理完成，正在生成最終 Excel 報告...", "status": "processing"})
    # 7. Create the output Excel file
    output_excel_bytes = create_excel_output(original_excel_content, aoai_result, query_data)

    return output_excel_bytes
