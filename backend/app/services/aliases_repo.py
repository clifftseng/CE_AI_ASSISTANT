from typing import List, Dict, Any
from app.db.mongo import get_db
from app.models.schemas import FieldAlias

class AliasesRepository:
    def __init__(self):
        self.collection = get_db()["field_aliases"]

    async def resolve(self, candidates: List[str]) -> Dict[str, str | None]:
        # Normalize candidates for lookup
        normalized_candidates = [self._normalize_string(c) for c in candidates]
        
        # Find aliases that match any of the normalized candidates
        # We need to search in the 'aliases' array field
        results = await self.collection.find({"aliases": {"$in": normalized_candidates}}).to_list(None)
        
        mapping = {candidate: None for candidate in candidates}
        for doc in results:
            canonical = doc["canonical"]
            for alias in doc["aliases"]:
                if alias in normalized_candidates:
                    # Map the original candidate to its canonical form
                    # This assumes a 1:1 mapping for simplicity, first match wins
                    original_candidate_index = normalized_candidates.index(alias)
                    mapping[candidates[original_candidate_index]] = canonical
        return mapping

    async def batch_upsert(self, items: List[FieldAlias]):
        operations = []
        for item in items:
            normalized_canonical = self._normalize_string(item.canonical)
            normalized_aliases = [self._normalize_string(alias) for alias in item.aliases]
            
            # Ensure canonical is also in aliases for self-resolution
            if normalized_canonical not in normalized_aliases:
                normalized_aliases.append(normalized_canonical)

            operations.append({
                "update_one": {
                    "filter": {"canonical": normalized_canonical},
                    "update": {"$set": {"aliases": normalized_aliases}},
                    "upsert": True
                }
            })
        
        if operations:
            await self.collection.bulk_write(operations)

    def _normalize_string(self, text: str) -> str:
        # This should be consistent with parts_repo.py
        text = text.strip()
        text = text.lower()
        text = " ".join(text.split())
        text = text.replace(" (", "(").replace(") ", ")")
        return text
