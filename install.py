import asyncio
from sqlalchemy import text
from database import async_engine
from models import User, Reminder, Base

async def init_database():
    print("🚀 Начинаю инициализацию базы данных...")
    
    async with async_engine.begin() as conn:
        # Включаем расширение для UUID (нужно для JWT ID в RevokedToken)
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Таблицы успешно созданы:")
        print("   - users")
        print("   - reminders")
        
        # Проверяем, что таблицы действительно создались
        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ))
        tables = [row[0] for row in result.fetchall()]
        print(f"\n📋 Таблицы в БД: {', '.join(tables)}")


async def main():
    await init_database()

if __name__ == "__main__":
    asyncio.run(main())