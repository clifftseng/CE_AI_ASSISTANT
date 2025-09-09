import asyncio
from datetime import datetime
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.services.parts_repo import PartsRepository
from app.services.aliases_repo import AliasesRepository
from app.models.schemas import Part, SpecItem, SourceFile, FieldAlias

async def seed_data():
    await connect_to_mongo()
    parts_repo = PartsRepository()
    aliases_repo = AliasesRepository()

    print("Seeding parts data...")
    # Seed a part
    part_no_1 = "uP8308PDN8-3K"
    await parts_repo.upsert_specs(
        partNo=part_no_1,
        items=[
            SpecItem(
                key="Overcharge Release Voltage (Ref)",
                value=4.25,
                unit="V",
                aliases=["OCV", "Overcharge Voltage"],
                status="confirmed",
                lastUpdatedAt=datetime.now(),
                lastUpdatedBy="seed_script",
                sourceFiles=[SourceFile(filename="datasheet_up8308.pdf", uploadedAt=datetime.now())]
            ),
            SpecItem(
                key="Operating Temperature Range",
                value="-40 to 85",
                unit="°C",
                aliases=["Temp Range", "Operating Temp"],
                status="confirmed",
                lastUpdatedAt=datetime.now(),
                lastUpdatedBy="seed_script",
                notes="From manufacturer datasheet"
            )
        ],
        actor="seed_script",
        sourceFilename="initial_seed.py"
    )
    print(f"Part {part_no_1} seeded.")

    print("Seeding field aliases data...")
    # Seed field aliases
    await aliases_repo.batch_upsert([
        FieldAlias(
            canonical="Overcharge Release Voltage (Ref)",
            aliases=["OCV", "Overcharge Voltage", "過充釋放電壓"]
        ),
        FieldAlias(
            canonical="Operating Temperature Range",
            aliases=["Temp Range", "Operating Temp", "工作溫度範圍"]
        )
    ])
    print("Field aliases seeded.")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(seed_data())
