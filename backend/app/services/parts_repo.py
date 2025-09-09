from datetime import datetime
from typing import List, Dict, Any
from bson import ObjectId
from app.db.mongo import get_db
from app.models.schemas import Part, SpecItem, SourceFile

class PartsRepository:
    def __init__(self):
        self.collection = get_db()["parts"]

    async def get_part(self, partNo: str) -> Part | None:
        part_data = await self.collection.find_one({"partNo": partNo})
        if part_data:
            # Convert _id to str for Pydantic compatibility if needed
            if "_id" in part_data: # Ensure _id is handled if present
                part_data["id"] = str(part_data["_id"])
                del part_data["_id"]
            return Part(**part_data)
        return None

    async def upsert_specs(self, partNo: str, items: List[SpecItem], actor: str, sourceFilename: str | None = None):
        current_time = datetime.now()

        # Normalize partNo
        normalized_partNo = self._normalize_string(partNo)

        # Prepare specs for update
        specs_to_upsert = []
        for item in items:
            normalized_key = self._normalize_string(item.key)
            normalized_aliases = [self._normalize_string(alias) for alias in item.aliases]

            spec_data = item.model_dump(exclude_unset=True) # Use model_dump for Pydantic v2
            spec_data["key"] = normalized_key
            spec_data["aliases"] = normalized_aliases
            spec_data["lastUpdatedAt"] = current_time
            spec_data["lastUpdatedBy"] = actor
            
            if sourceFilename:
                source_file = SourceFile(filename=sourceFilename, uploadedAt=current_time)
                # Check if sourceFiles already exists and append, otherwise create list
                if "sourceFiles" in spec_data and isinstance(spec_data["sourceFiles"], list):
                    spec_data["sourceFiles"].append(source_file.model_dump())
                else:
                    spec_data["sourceFiles"] = [source_file.model_dump()]

            specs_to_upsert.append(spec_data)

        # Find existing part or create a new one
        existing_part = await self.collection.find_one({"partNo": normalized_partNo})

        if existing_part:
            # Update existing part
            update_fields = {"updatedAt": current_time}
            for new_spec in specs_to_upsert:
                # Find if spec with same key exists
                found = False
                for i, existing_spec in enumerate(existing_part.get("specs", [])):
                    if existing_spec["key"] == new_spec["key"]:
                        # Update existing spec
                        existing_part["specs"][i] = new_spec
                        found = True
                        break
                if not found:
                    # Add new spec
                    existing_part.setdefault("specs", []).append(new_spec)
            
            update_fields["specs"] = existing_part["specs"]
            await self.collection.update_one(
                {"partNo": normalized_partNo},
                {"$set": update_fields}
            )
        else:
            # Create new part
            new_part = Part(
                partNo=normalized_partNo,
                specs=specs_to_upsert,
                createdAt=current_time,
                updatedAt=current_time
            )
            await self.collection.insert_one(new_part.model_dump())

    def _normalize_string(self, text: str) -> str:
        # Trim whitespace
        text = text.strip()
        # Convert to lowercase
        text = text.lower()
        # Replace multiple spaces with a single space
        text = " ".join(text.split())
        # Remove spaces around parentheses
        text = text.replace(" (", "(").replace(") ", ")")
        return text
