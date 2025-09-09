from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
from datetime import datetime

# --- Parts API Schemas ---

class SpecUpdateItem(BaseModel):
    keyOrAlias: str
    value: str | int | None = None
    unit: str | None = None
    sourceFilename: str | None = None

class PatchSpecsRequest(BaseModel):
    items: List[SpecUpdateItem]
    actor: str

class UpdatedSpecResponse(BaseModel):
    key: str
    value: str | int | None
    unit: str | None = None
    status: Literal["confirmed", "edited", "incorrect", "pending"]
    lastUpdatedAt: datetime
    lastUpdatedBy: str
    sourceFiles: List[Dict[str, Any]] = [] # Using Dict[str, Any] as SourceFile is not directly a Pydantic model here
    aliasUnresolved: bool = False # Indicates if the keyOrAlias could not be resolved

class PatchSpecsResponse(BaseModel):
    updated_specs: List[UpdatedSpecResponse]
    unresolved_aliases: List[str] = []

class MarkIncorrectRequest(BaseModel):
    keysOrAliases: List[str]
    note: str | None = None
    actor: str

# --- Aliases API Schemas ---

class ResolveAliasesRequest(BaseModel):
    keys: List[str]

class ResolveAliasesResponse(BaseModel):
    mappings: Dict[str, str] # candidate -> canonical

class BatchUpsertAliasItem(BaseModel):
    canonical: str
    aliases: List[str]

class BatchUpsertAliasesRequest(BaseModel):
    items: List[BatchUpsertAliasItem]
