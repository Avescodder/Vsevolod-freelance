import aiosqlite
import asyncio


async def creation_database(path: str):
    async with aiosqlite.connect(path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS dialogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id TEXT,
                status INTEGER,
                chat_id TEXT,
                reason TEXT,
                phone_number TEXT
            )
        """)
        await db.commit()
async def main():
    path = "db_avito.sqlite3"
    create_task = asyncio.create_task(creation_database(path))
    await create_task
if __name__ == "__main__":
    asyncio.run(main())

