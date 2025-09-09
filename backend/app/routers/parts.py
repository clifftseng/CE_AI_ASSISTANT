from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from app.db.mongo import get_db
from app.services.parts_repo import PartsRepository
from app.services.aliases_repo import AliasesRepository
from app.models import api_schemas, schemas

router = APIRouter()

# Dependency to get PartsRepository instance
def get_parts_repo() -> PartsRepository:
    return PartsRepository()

# Dependency to get AliasesRepository instance
def get_aliases_repo() -> AliasesRepository:
    return AliasesRepository()

@router.get("/{partNo}", response_model=schemas.Part)
async def get_part(partNo: str, parts_repo: PartsRepository = Depends(get_parts_repo)):
    part = await parts_repo.get_part(partNo)
    if not part:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found")
    return part

@router.patch("/{partNo}/specs", response_model=api_schemas.PatchSpecsResponse)
async def patch_specs(
    partNo: str,
    request: api_schemas.PatchSpecsRequest,
    parts_repo: PartsRepository = Depends(get_parts_repo),
    aliases_repo: AliasesRepository = Depends(get_aliases_repo)
):
    updated_specs_response: List[api_schemas.UpdatedSpecResponse] = []
    unresolved_aliases: List[str] = []
    specs_to_upsert: List[schemas.SpecItem] = []

    # Resolve all keyOrAliases first
    keys_to_resolve = [item.keyOrAlias for item in request.items]
    resolved_mappings = await aliases_repo.resolve(keys_to_resolve)

    for item in request.items:
        canonical_key = resolved_mappings.get(item.keyOrAlias)

        if not canonical_key:
            unresolved_aliases.append(item.keyOrAlias)
            # Add a placeholder for unresolved aliases in the response
            updated_specs_response.append(api_schemas.UpdatedSpecResponse(
                key=item.keyOrAlias, # Use original key for unresolved
                value=item.value,
                unit=item.unit,
                status="pending", # Default to pending if unresolved
                lastUpdatedAt=datetime.now(),
                lastUpdatedBy=request.actor,
                aliasUnresolved=True
            ))
            continue

        # Fetch existing part to determine status
        existing_part = await parts_repo.get_part(partNo)
        existing_spec = None
        if existing_part:
            for spec in existing_part.specs:
                if spec.key == canonical_key:
                    existing_spec = spec
                    break

        spec_status = "edited" if existing_spec else "pending"

        source_files = []
        if existing_spec and existing_spec.sourceFiles:
            source_files = [sf.model_dump() for sf in existing_spec.sourceFiles] # Convert to dict for modification

        if item.sourceFilename:
            new_source_file = schemas.SourceFile(filename=item.sourceFilename, uploadedAt=datetime.now())
            # Check if source file with same name exists and replace it
            found_source = False
            for i, sf in enumerate(source_files):
                if sf["filename"] == new_source_file.filename:
                    source_files[i] = new_source_file.model_dump()
                    found_source = True
                    break
            if not found_source:
                source_files.append(new_source_file.model_dump())

        spec_item = schemas.SpecItem(
            key=canonical_key,
            value=item.value,
            unit=item.unit,
            aliases=existing_spec.aliases if existing_spec else [], # Preserve existing aliases
            status=spec_status,
            sourceFiles=[schemas.SourceFile(**sf) for sf in source_files], # Convert back to Pydantic model
            lastUpdatedAt=datetime.now(),
            lastUpdatedBy=request.actor,
            notes=existing_spec.notes if existing_spec else None # Preserve existing notes
        )
        specs_to_upsert.append(spec_item)

        updated_specs_response.append(api_schemas.UpdatedSpecResponse(
            key=canonical_key,
            value=item.value,
            unit=item.unit,
            status=spec_status,
            lastUpdatedAt=spec_item.lastUpdatedAt,
            lastUpdatedBy=spec_item.lastUpdatedBy,
            sourceFiles=source_files,
            aliasUnresolved=False
        ))

    if specs_to_upsert:
        await parts_repo.upsert_specs(partNo, specs_to_upsert, request.actor, None) # sourceFilename handled internally

    return api_schemas.PatchSpecsResponse(
        updated_specs=updated_specs_response,
        unresolved_aliases=unresolved_aliases
    )

@router.post("/{partNo}/specs/mark-incorrect", response_model=Dict[str, Any])
async def mark_specs_incorrect(
    partNo: str,
    request: api_schemas.MarkIncorrectRequest,
    parts_repo: PartsRepository = Depends(get_parts_repo),
    aliases_repo: AliasesRepository = Depends(get_aliases_repo)
):
    # Resolve all keyOrAliases first
    keys_to_resolve = request.keysOrAliases
    resolved_mappings = await aliases_repo.resolve(keys_to_resolve)

    canonical_keys_to_mark = []
    unresolved_mark_aliases = []

    for key_or_alias in keys_to_resolve:
        canonical_key = resolved_mappings.get(key_or_alias)
        if canonical_key:
            canonical_keys_to_mark.append(canonical_key)
        else:
            unresolved_mark_aliases.append(key_or_alias)

    if not canonical_keys_to_mark:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No valid keys/aliases provided or resolved: {unresolved_mark_aliases}"
        )

    # Fetch the part
    part = await parts_repo.get_part(partNo)
    if not part:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found")

    # Update specs
    updated_count = 0
    for spec in part.specs:
        if spec.key in canonical_keys_to_mark:
            spec.status = "incorrect"
            spec.notes = request.note # Overwrite or set note
            spec.lastUpdatedAt = datetime.now()
            spec.lastUpdatedBy = request.actor
            updated_count += 1

    if updated_count > 0:
        # Use upsert_specs to update the part with modified specs
        # This will overwrite the existing specs with the updated ones
        await parts_repo.upsert_specs(partNo, part.specs, request.actor, None)

    return {"message": f"Successfully marked {updated_count} specs as incorrect.", "unresolved_aliases": unresolved_mark_aliases}
