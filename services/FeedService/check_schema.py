import asyncio
import sys
sys.path.insert(0, ".")

async def check():
    from sqlalchemy import text
    from src.lib.db import engine
    
    sql = (
        "SELECT column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_name = 'post_tags' "
        "ORDER BY ordinal_position"
    )
    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        print("=== post_tags schema ===")
        for row in result:
            print(dict(row._mapping))

        result2 = await conn.execute(text(
            "SELECT column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_name = 'tags' "
            "ORDER BY ordinal_position"
        ))
        print("\n=== tags schema ===")
        for row in result2:
            print(dict(row._mapping))

        result3 = await conn.execute(text("SELECT name FROM tags LIMIT 5"))
        print("\n=== sample tags ===")
        for row in result3:
            print(dict(row._mapping))

asyncio.run(check())
