import os
import json
from typing import List, Dict, Any, Tuple
import pandas as pd
import datetime
from pathlib import Path

# 從 aoai_method 導入設定與工具
from aoai_method.aoai_service import client, pretty_print_json, extract_first_json_block
from app.core.config import settings # 使用 backend 的 settings

def build_user_payload(
    docs: List[Dict[str, Any]],
    pns: List[str],
    items: List[str],
    language: str = "zh-TW",
    return_source_excerpt: bool = True
) -> Dict[str, Any]:
    """建構要傳送給 LLM 的 user payload。"""
    return {
        "docs": docs,
        "targets": {
            "pns": pns,
            "items": items
        },
        "options": {
            "suffix_map": {},
            "language": language,
            "return_source_excerpt": return_source_excerpt
        },
        "excel_context": {}
    }

async def call_aoai_extractor(system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    呼叫 AOAI chat completion API 並要求 JSON 輸出。
    """
    print("\n正在呼叫 AOAI API...")
    try:
        # 使用 backend 的 settings.AZURE_OPENAI_DEPLOYMENT
        rsp = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = rsp.choices[0].message.content
        
        # 嘗試解析 JSON，如果失敗，嘗試從 markdown block 中提取
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print("[警告] AOAI 回應不是一個完美的 JSON，嘗試從程式碼區塊中提取...")
            json_block = extract_first_json_block(content)
            if json_block:
                try:
                    return json.loads(json_block)
                except json.JSONDecodeError:
                    print("[錯誤] 從程式碼區塊中提取的內容仍然不是有效的 JSON。")
                    raise ValueError(f"無法解析 LLM 回應: {content}")
            else:
                raise ValueError(f"在 LLM 回應中找不到 JSON 區塊: {content}")

    except Exception as e:
        print(f"[錯誤] 呼叫 AOAI API 時發生問題: {e}")
        return {"error": str(e)}

def write_summary_to_excel(original_excel_path: Path, query_data: Dict, aoai_result: Dict, output_dir: Path) -> Path:
    """
    將 AOAI 抽取結果寫入 Excel 檔案 (summary.xlsx)。
    第一個工作表為總結，後續工作表為每個 target_pn 的詳細資訊。
    """
    # 生成帶時間戳的檔名
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_filename = f"summary_{timestamp}.xlsx"
    print(f"\n正在將結果寫入 {output_dir / output_filename}...")
    
    # 確保 output 目錄存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 讀取原始 Excel 檔案
    try:
        original_df = pd.read_excel(original_excel_path, sheet_name=0, header=None)
    except Exception as e:
        print(f"[錯誤] 無法讀取原始 Excel 檔案 {original_excel_path}: {e}")
        raise

    # 建立查詢欄位和目標的索引映射
    query_fields = query_data["query_fields"]
    query_targets = query_data["query_targets"]

    # 建立 field 到 row index 的映射 (從第二行開始，因為第一行是 header)
    field_to_row_idx = {field: i  for i, field in enumerate(query_fields)}
    # 建立 target_pn 到 column index 的映射 (從第二列開始，因為第一列是 query_fields)
    pn_to_col_idx = {pn: i + 1 for i, pn in enumerate(query_targets)}

    # 複製一份 DataFrame 用於 Summary Sheet
    summary_df = original_df.copy()

    # 確保 summary_df 有足夠的行和列來容納所有數據
    max_row_needed = max(field_to_row_idx.values()) if field_to_row_idx else 0
    max_col_needed = max(pn_to_col_idx.values()) if pn_to_col_idx else 0

    current_rows, current_cols = summary_df.shape

    # 擴展行
    if max_row_needed >= current_rows:
        rows_to_add = max_row_needed - current_rows + 1
        summary_df = summary_df.reindex(range(current_rows + rows_to_add), axis=0)

    # 擴展列
    if max_col_needed >= current_cols:
        cols_to_add = max_col_needed - current_cols + 1
        summary_df = summary_df.reindex(range(current_cols + cols_to_add), axis=1)

    # 填充 Summary Sheet
    for doc in aoai_result.get("documents", []):
        target_pn = doc.get("target_pn")
        if target_pn in pn_to_col_idx:
            col_idx = pn_to_col_idx[target_pn]
            for item in doc.get("items", []):
                field = item.get("field")
                value = item.get("value")
                if field in field_to_row_idx:
                    row_idx = field_to_row_idx[field]
                    summary_df.iloc[row_idx, col_idx] = str(value) if isinstance(value, (dict, list)) else value

    # 寫入 Excel 檔案
    output_excel_path = output_dir / output_filename
    with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
        # 寫入 Summary Sheet
        summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)

        # 寫入 Detail Sheets
        for doc in aoai_result.get("documents", []):
            target_pn = doc.get("target_pn")
            if target_pn:
                detail_data = []
                for item in doc.get("items", []):
                    detail_data.append({
                        "Field": item.get("field", ""),
                        "Value": item.get("value", "N/A"),
                        "Unit": item.get("unit", None),
                        "Confidence": item.get("confidence", 0.0),
                        "Provenance": item.get("provenance", ""),
                        "Notes": item.get("notes", "")
                    })
                detail_df = pd.DataFrame(detail_data)
                sheet_name = target_pn.replace(" ", "_").replace("/", "_")[:31]
                detail_df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"  - 結果已成功寫入 {output_excel_path}")
    return output_excel_path
