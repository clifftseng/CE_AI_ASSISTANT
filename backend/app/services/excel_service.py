
import pandas as pd
from typing import Dict, Tuple, List, Any
from fastapi import UploadFile
import io

def get_excel_query_data_from_path(file_path: str) -> Dict:
    """
    Reads query data from an Excel file path.
    """
    df_row1 = pd.read_excel(file_path, sheet_name=0, header=None, nrows=1)
    df_colA = pd.read_excel(file_path, sheet_name=0, header=None, usecols="A")

    query_fields = df_colA.iloc[:, 0].dropna().tolist()
    query_targets = df_row1.iloc[0, 1:].dropna().tolist()

    # Clean up the list, keeping only non-empty strings
    query_fields = [field for field in query_fields if str(field).strip()] 
    query_targets = [target for target in query_targets if str(target).strip()] 

    return {
        "query_fields": query_fields,
        "query_targets": query_targets
    }

def create_excel_output(original_excel_content: bytes, results: List[Dict[str, Any]], query_data: Dict) -> bytes:
    """
    Updates the Excel file with the AOAI results and returns it as bytes.
    """
    df = pd.read_excel(io.BytesIO(original_excel_content))

    # Create a map for quick lookup: field_name -> row_index
    field_to_row = {field: i + 1 for i, field in enumerate(query_data["query_fields"]) if field in df.iloc[:, 0].values}

    # Create a map for quick lookup: target_pn -> col_index
    target_to_col = {target: i + 1 for i, target in enumerate(query_data["query_targets"]) if target in df.columns}

    # Populate the dataframe with results
    for doc in results.get("documents", []):
        target_pn = doc.get("target_pn")
        if target_pn not in target_to_col:
            continue

        col_idx = target_to_col[target_pn]

        for item in doc.get("items", []):
            field = item.get("field")
            if field not in field_to_row:
                continue

            row_idx = field_to_row[field]
            value_to_write = item.get("value", "N/A")
            
            # df.at is 0-indexed for rows, but columns are referenced by name
            # We need to map our 1-based excel indices to 0-based df indices
            df.at[row_idx -1, df.columns[col_idx]] = value_to_write

    # Write to an in-memory buffer
    output_buffer = io.BytesIO()
    with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    return output_buffer.getvalue()
