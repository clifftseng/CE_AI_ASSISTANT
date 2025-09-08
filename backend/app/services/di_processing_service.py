# backend/app/services/di_processing_service.py
from typing import List, Dict, Any, Tuple

def _structure_di_tables(di_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforms DI tables into a structured list of table objects."""
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

        rows_dict: Dict[int, Dict[int, str]] = {}
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
            row_list: List[str] = []
            for c_idx in range(max_cols + 1):
                row_list.append(rows_dict[r_idx].get(c_idx, ""))
            table_object["rows"].append(row_list)
        
        structured_tables.append(table_object)
        
    return structured_tables

def _is_point_inside_bounding_box(x: float, y: float, polygon: List[Dict[str, float]]) -> bool:
    """
    Checks if a point (x, y) is inside a polygon's bounding box.
    """
    if not polygon:
        return False
    min_x = min(p['x'] for p in polygon)
    max_x = max(p['x'] for p in polygon)
    min_y = min(p['y'] for p in polygon)
    max_y = max(p['y'] for p in polygon)
    return min_x <= x <= max_x and min_y <= y <= max_y

def _extract_text_by_page(di_pages: List[Dict[str, Any]], di_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts line content from each page, excluding any lines that fall within a table's bounding box.
    """
    table_polygons_by_page: Dict[int, List[List[Dict[str, float]]]] = {}
    for table in di_tables:
        for region in table.get("bounding_regions", []):
            page_num = region.get("page_number")
            if page_num not in table_polygons_by_page:
                table_polygons_by_page[page_num] = []
            if region.get("polygon"):
                table_polygons_by_page[page_num].append(region["polygon"])

    page_contents = []
    for page in di_pages:
        page_number = page.get("page_number")
        table_polygons = table_polygons_by_page.get(page_number, [])
        
        non_table_lines = []
        for line in page.get("lines", []):
            if not line.get("polygon"):
                continue
            
            line_x, line_y = line["polygon"][0]['x'], line["polygon"][0]['y']
            
            is_in_table = False
            for table_poly in table_polygons:
                if _is_point_inside_bounding_box(line_x, line_y, table_poly):
                    is_in_table = True
                    break
            
            if not is_in_table:
                non_table_lines.append(line.get("content", ""))

        full_page_content = "\n".join(non_table_lines)
        page_contents.append({
            "page_number": page_number,
            "content": full_page_content
        })
        
    return page_contents

def create_structured_document(di_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes raw DI data and returns a structured dictionary with processed pages and tables.
    """
    print("\n=== Structuring page and table content (from di_processing_service) ===")
    structured_tables = _structure_di_tables(di_data.get("tables", []))
    page_content = _extract_text_by_page(di_data.get("pages", []), di_data.get("tables", []))

    combined_output = {
        "pages": page_content,
        "tables": structured_tables
    }
    return combined_output
