# backend/app/services/excel_processing_service.py
import asyncio
import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

import pandas as pd
from app.models.schemas import ExcelQuery

async def get_excel_query_data(excel_path: Path) -> ExcelQuery:
    """
    Reads query data from a single Excel file asynchronously.
    
    Args:
        excel_path: Path to the Excel file.

    Returns:
        An ExcelQuery object containing the query data.
    """
    def read_excel():
        try:
            # Read the first row for Query Targets
            df_row1 = pd.read_excel(excel_path, sheet_name=0, header=None, nrows=1)
            # Read the first column for Query Fields
            df_colA = pd.read_excel(excel_path, sheet_name=0, header=None, usecols="A")
        except Exception as e:
            raise IOError(f"Failed to read or parse the Excel file: {e}")
        
        # Get "Query Fields" (non-empty values from A1, A2, ...)
        query_fields = df_colA.iloc[:, 0].dropna().tolist()

        # Get "Query Targets" (non-empty values from B1, C1, ...)
        query_targets = df_row1.iloc[0, 1:].dropna().tolist()

        return ExcelQuery(
            query_fields=query_fields,
            query_targets=query_targets
        )

    print(f"Reading Excel file: {excel_path}")
    return await asyncio.to_thread(read_excel)

async def write_summary_to_excel(
    original_excel_path: Path, 
    query_data: ExcelQuery, 
    aoai_result: Dict[str, Any], 
    output_dir: Path
) -> Path:
    """
    Writes the AOAI extraction result to a new Excel file asynchronously.
    The first sheet is a summary, and subsequent sheets contain details for each target_pn.
    
    Args:
        original_excel_path: Path to the original Excel file.
        query_data: The ExcelQuery object with fields and targets.
        aoai_result: The dictionary result from the AOAI service.
        output_dir: The directory to save the output file in.

    Returns:
        The path to the newly created summary Excel file.
    """
    def write_excel():
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_filename = f"summary_{timestamp}.xlsx"
        output_excel_path = output_dir / output_filename
        
        print(f"\nWriting results to {output_excel_path}...")
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            original_df = pd.read_excel(original_excel_path, sheet_name=0, header=None)
        except Exception as e:
            print(f"[ERROR] Could not read original Excel file {original_excel_path}: {e}")
            raise

        field_to_row_idx = {field: i for i, field in enumerate(query_data.query_fields)}
        pn_to_col_idx = {pn: i + 1 for i, pn in enumerate(query_data.query_targets)}
        
        summary_df = original_df.copy()

        # --- Resize DataFrame if necessary ---
        max_row_needed = max(field_to_row_idx.values()) if field_to_row_idx else 0
        max_col_needed = max(pn_to_col_idx.values()) if pn_to_col_idx else 0
        current_rows, current_cols = summary_df.shape

        if max_row_needed >= current_rows:
            summary_df = summary_df.reindex(range(max_row_needed + 1), axis=0)
        if max_col_needed >= current_cols:
            summary_df = summary_df.reindex(range(max_col_needed + 1), axis=1)

        # --- Fill Summary Sheet ---
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

        # --- Write to Excel file ---
        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)

            for doc in aoai_result.get("documents", []):
                target_pn = doc.get("target_pn")
                if not target_pn:
                    continue
                
                detail_data = [
                    {
                        "Field": item.get("field", ""),
                        "Value": item.get("value", "N/A"),
                        "Unit": item.get("unit"),
                        "Confidence": item.get("confidence", 0.0),
                        "Provenance": item.get("provenance", ""),
                        "Notes": item.get("notes", "")
                    } for item in doc.get("items", [])
                ]
                detail_df = pd.DataFrame(detail_data)
                sheet_name = target_pn.replace(" ", "_").replace("/", "_")[:31]
                detail_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"  - Successfully wrote results to {output_excel_path}")
        return output_excel_path

    return await asyncio.to_thread(write_excel)
