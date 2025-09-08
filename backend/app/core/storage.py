import aiofiles
import uuid
from pathlib import Path
from fastapi import UploadFile
from typing import Dict, Union

from .config import settings

download_registry: Dict[str, Path] = {}

class StorageService:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> Path:
        safe_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = self.base_dir / safe_filename
        
        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                while content := await file.read(1024 * 1024):
                    await out_file.write(content)
        finally:
            await file.close()
            
        return file_path

    def make_downloadable(self, file_path: Path) -> str:
        file_id = str(uuid.uuid4())
        download_registry[file_id] = file_path
        return f"/api/download/{file_id}"

    def resolve_download_path(self, file_id: str) -> Path | None:
        return download_registry.get(file_id)

    async def read_file_bytes(self, file_path: Path) -> bytes:
        """
        Reads the content of a file as bytes asynchronously.
        """
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
        return content

storage_service = StorageService(settings.DATA_DIR)
