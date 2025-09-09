# backend/app/models/schemas.py
from pydantic import BaseModel
from typing import List
from datetime import datetime

# --- Core Data Models ---

class ExcelQuery(BaseModel):
    """Fields parsed from the first column (query_fields) and
    the first row after A1 (query_targets) of the Excel file."""
    query_fields: List[str]
    query_targets: List[str]

# --- API Response Models ---

class JobResponse(BaseModel):
    job_id: str

class ValueResultResponse(BaseModel):
    status: str
    download_url: str | None
    query_fields: List[str] | None = None
    query_targets: List[str] | None = None

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

# --- MongoDB Models ---

class SourceFile(BaseModel):
    filename: str
    uploadedAt: datetime

class SpecItem(BaseModel):
    key: str
    value: str | int | None
    unit: str | None = None
    aliases: List[str] = []
    status: str # "confirmed"|"edited"|"incorrect"|"pending"
    sourceFiles: List[SourceFile] = []
    lastUpdatedAt: datetime
    lastUpdatedBy: str
    notes: str | None = None

class Part(BaseModel):
    partNo: str
    manufacturer: str | None = None
    specs: List[SpecItem] = []
    createdAt: datetime
    updatedAt: datetime

class FieldAlias(BaseModel):
    canonical: str
    aliases: List[str] = []