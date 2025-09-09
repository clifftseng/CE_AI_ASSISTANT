from fastapi import APIRouter, Depends
from typing import List, Dict

from app.services.aliases_repo import AliasesRepository
from app.models import api_schemas, schemas

router = APIRouter()

# Dependency to get AliasesRepository instance
def get_aliases_repo() -> AliasesRepository:
    return AliasesRepository()

@router.post("/resolve", response_model=api_schemas.ResolveAliasesResponse)
async def resolve_aliases(
    request: api_schemas.ResolveAliasesRequest,
    aliases_repo: AliasesRepository = Depends(get_aliases_repo)
):
    mappings = await aliases_repo.resolve(request.keys)
    return api_schemas.ResolveAliasesResponse(mappings=mappings)

@router.post("/batch-upsert", status_code=204) # No content response
async def batch_upsert_aliases(
    request: api_schemas.BatchUpsertAliasesRequest,
    aliases_repo: AliasesRepository = Depends(get_aliases_repo)
):
    # Convert BatchUpsertAliasItem to FieldAlias for the repository
    field_aliases = [schemas.FieldAlias(canonical=item.canonical, aliases=item.aliases) for item in request.items]
    await aliases_repo.batch_upsert(field_aliases)
    return
