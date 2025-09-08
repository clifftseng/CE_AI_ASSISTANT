import pytest
from fastapi import UploadFile, HTTPException
from io import BytesIO
from unittest.mock import MagicMock

from app.utils.file_validation import validate_file, validate_files
from app.core.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        MAX_FILE_SIZE_MB=1,
        TOTAL_UPLOAD_LIMIT_MB=2,
        ALLOWED_EXCEL_EXTS=".xlsx,.xls",
        ALLOWED_PDF_EXTS=".pdf"
    )

def test_validate_file_success(mock_settings):
    mock_file = UploadFile(filename="test.xlsx", file=BytesIO(b"small file"))
    mock_file.size = 100
    try:
        validate_file(mock_file, mock_settings.ALLOWED_EXCEL_EXTS.split(','), mock_settings.MAX_FILE_SIZE_MB)
    except HTTPException:
        pytest.fail("Validation should pass for a valid file.")

def test_validate_file_wrong_extension(mock_settings):
    mock_file = UploadFile(filename="test.txt", file=BytesIO(b"some data"))
    mock_file.size = 100
    with pytest.raises(HTTPException) as excinfo:
        validate_file(mock_file, mock_settings.ALLOWED_EXCEL_EXTS.split(','), mock_settings.MAX_FILE_SIZE_MB)
    assert excinfo.value.status_code == 400
    assert "檔案類型錯誤" in excinfo.value.detail

def test_validate_file_too_large(mock_settings):
    large_content = b"a" * (2 * 1024 * 1024)
    mock_file = UploadFile(filename="large.xlsx", file=BytesIO(large_content))
    mock_file.size = len(large_content)
    with pytest.raises(HTTPException) as excinfo:
        validate_file(mock_file, mock_settings.ALLOWED_EXCEL_EXTS.split(','), mock_settings.MAX_FILE_SIZE_MB)
    assert excinfo.value.status_code == 413
    assert "大小超過限制" in excinfo.value.detail

def test_validate_files_success(mock_settings):
    file1 = UploadFile(filename="doc1.xlsx", file=BytesIO(b"excel data"))
    file1.size = 500 * 1024
    file2 = UploadFile(filename="report.pdf", file=BytesIO(b"pdf data"))
    file2.size = 1 * 1024 * 1024
    
    files = [file1, file2]
    try:
        validate_files(files, mock_settings)
    except HTTPException:
        pytest.fail("Validation should pass for valid multiple files.")

def test_validate_files_mixed_invalid_extension(mock_settings):
    file1 = UploadFile(filename="doc1.xlsx", file=BytesIO(b"excel data"))
    file1.size = 100
    file2 = UploadFile(filename="image.jpg", file=BytesIO(b"image data"))
    file2.size = 100
    
    files = [file1, file2]
    with pytest.raises(HTTPException) as excinfo:
        validate_files(files, mock_settings)
    assert excinfo.value.status_code == 400
    assert "不支援的檔案類型: 'image.jpg'" in excinfo.value.detail

def test_validate_files_total_size_exceeded(mock_settings):
    file1 = UploadFile(filename="large1.xlsx", file=BytesIO(b"a" * (1 * 1024 * 1024)))
    file1.size = 1 * 1024 * 1024
    file2 = UploadFile(filename="large2.pdf", file=BytesIO(b"b" * (1.5 * 1024 * 1024)))
    file2.size = 1.5 * 1024 * 1024
    
    files = [file1, file2]
    with pytest.raises(HTTPException) as excinfo:
        validate_files(files, mock_settings)
    assert excinfo.value.status_code == 413
    assert "上傳總大小超過限制" in excinfo.value.detail

def test_validate_files_single_file_too_large_in_batch(mock_settings):
    file1 = UploadFile(filename="small.xlsx", file=BytesIO(b"small"))
    file1.size = 100
    file2 = UploadFile(filename="too_large.pdf", file=BytesIO(b"a" * (1.5 * 1024 * 1024)))
    file2.size = 1.5 * 1024 * 1024
    
    files = [file1, file2]
    with pytest.raises(HTTPException) as excinfo:
        validate_files(files, mock_settings)
    assert excinfo.value.status_code == 413
    assert "檔案 'too_large.pdf' 大小超過限制" in excinfo.value.detail
