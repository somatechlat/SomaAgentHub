import asyncio
import asyncpg
import os

async def main():
    url = os.getenv("SOMA_AGENT_HUB_DATABASE_URL")
    print(f"Connecting to {url}...")
    try:
        conn = await asyncpg.connect(url)
        print("Successfully connected!")
        rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print("Tables:", [r['table_name'] for r in rows])
        await conn.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(main())
