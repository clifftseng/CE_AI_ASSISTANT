from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse # Import HTMLResponse
from app.core.storage import storage_service
from pathlib import Path
import pandas as pd # Import pandas

router = APIRouter()

@router.get("/{file_id}")
async def download_file(file_id: str):
    file_path: Path | None = storage_service.resolve_download_path(file_id)
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or expired.")
        
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type='application/octet-stream',
        headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
    )

@router.get("/preview/{file_id}", response_class=HTMLResponse)
async def preview_file(file_id: str):
    file_path: Path | None = storage_service.resolve_download_path(file_id)

    if not file_path or not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or expired.")
    
    if file_path.suffix.lower() not in ['.xlsx', '.xls']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Excel files can be previewed.")

    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(file_path)
        # Convert the DataFrame to an HTML table
        html_table = df.to_html(index=False, classes="table table-striped")
        return HTMLResponse(content=html_table)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to preview Excel file: {e}")
