import asyncio

import asyncpg


async def main():
    # Test with wrong password
    print("Test 1: wrong password")
    try:
        conn = await asyncpg.connect(
            user='finflow',
            password='wrong',
            database='finflow',
            host='127.0.0.1',
            port=5432
        )
        print("  SUCCESS (unexpected)")
        await conn.close()
    except asyncpg.InvalidPasswordError as e:
        print(f"  InvalidPasswordError: {e}")
    except asyncpg.PostgresError as e:
        print(f"  Other PostgresError: {e}")

    # Test with empty password
    print("Test 2: empty password")
    try:
        conn = await asyncpg.connect(
            user='finflow',
            password='',
            database='finflow',
            host='127.0.0.1',
            port=5432
        )
        print("  SUCCESS (unexpected)")
        await conn.close()
    except asyncpg.InvalidPasswordError as e:
        print(f"  InvalidPasswordError: {e}")
    except asyncpg.PostgresError as e:
        print(f"  Other PostgresError: {e}")

    # Test with correct password
    print("Test 3: correct password")
    try:
        conn = await asyncpg.connect(
            user='finflow',
            password='finflow',
            database='finflow',
            host='127.0.0.1',
            port=5432
        )
        result = await conn.fetchval('select 1')
        print(f"  SUCCESS: {result}")
        await conn.close()
    except asyncpg.InvalidPasswordError as e:
        print(f"  InvalidPasswordError: {e}")
    except asyncpg.PostgresError as e:
        print(f"  Other PostgresError: {e}")


asyncio.run(main())
