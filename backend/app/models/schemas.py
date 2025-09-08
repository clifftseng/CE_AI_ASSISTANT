from pydantic import BaseModel
from typing import List # Added List import

# --- API Response Models ---

class JobResponse(BaseModel):
    job_id: str

class ValueResultResponse(BaseModel):
    status: str
    download_url: str | None
    query_fields: List[str] | None = None # Added
    query_targets: List[str] | None = None # Added

class SSEProgress(BaseModel):
    percent: int
    message: str

class SSEPartial(BaseModel):
    text: str

class SSEDone(BaseModel):
    download_url: str

class SSEMetadata(BaseModel):
    query_fields: List[str]
    query_targets: List[str]