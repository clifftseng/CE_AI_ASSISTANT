from fastapi import UploadFile, HTTPException, status
from typing import List
from pathlib import Path

def validate_file(file: UploadFile, allowed_extensions: List[str], max_size_mb: int):
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"檔案類型錯誤。檔案 '{file.filename}' 只接受 {', '.join(allowed_extensions)} 格式。"
        )
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size is not None and file.size > max_size_bytes:
         raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"檔案 '{file.filename}' 大小超過限制 ({max_size_mb} MB)。"
        )

def validate_files(files: List[UploadFile], settings):
    total_size = 0
    excel_exts = [ext.strip() for ext in settings.ALLOWED_EXCEL_EXTS.split(',')]
    pdf_exts = [ext.strip() for ext in settings.ALLOWED_PDF_EXTS.split(',')]
    
    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext in excel_exts:
            validate_file(file, excel_exts, settings.MAX_FILE_SIZE_MB)
        elif file_ext in pdf_exts:
            validate_file(file, pdf_exts, settings.MAX_FILE_SIZE_MB)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支援的檔案類型: '{file.filename}'。只接受 Excel ({settings.ALLOWED_EXCEL_EXTS}) 或 PDF ({settings.ALLOWED_PDF_EXTS})。"
            )
        
        if file.size is not None:
            total_size += file.size

    if total_size > settings.TOTAL_UPLOAD_LIMIT_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"上傳總大小 ({total_size / (1024 * 1024):.2f} MB) 超過限制 ({settings.TOTAL_UPLOAD_LIMIT_MB} MB)。"
        )
