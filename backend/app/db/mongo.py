from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

class MongoClient:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

mongo_client = MongoClient()

async def connect_to_mongo():
    mongo_client.client = AsyncIOMotorClient(settings.MONGODB_URI)
    mongo_client.db = mongo_client.client[settings.MONGODB_DB]
    print("Connected to MongoDB.")

async def close_mongo_connection():
    if mongo_client.client:
        mongo_client.client.close()
        print("MongoDB connection closed.")

def get_client() -> AsyncIOMotorClient:
    return mongo_client.client

def get_db() -> AsyncIOMotorDatabase:
    return mongo_client.db

async def ping_mongodb():
    try:
        await mongo_client.db.command("ping")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
