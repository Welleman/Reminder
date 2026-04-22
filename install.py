import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from passlib.hash import pbkdf2_sha256 as pass256

from database import async_engine, AssyncSessionLocal
from models import User, Reminder, Role, Permission, NotificationLog, RevokedToken, AudiLog, Base

async def init_database():
    ''' Создание таблиц в БД '''
    
    async with async_engine.begin() as conn:
        # Включаем расширение для UUID (нужно для JWT ID в RevokedToken)
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)

        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ))

        tables = [row[0] for row in result.fetchall()]
        print(f"📋 В базе таблицы ({len(tables)}): {', '.join(tables)}")

async def create_permission(session: AsyncSession):
    ''' Добавление права доступа '''
    print("\n🔑 Создание прав доступа...")

    # Определяем все возможные права
    permissions_data = [
        # Пользователи
        ("users", "create", "Создание пользователей"),
        ("users", "read", "Просмотр пользователей"),
        ("users", "update", "Редактирование пользователей"),
        ("users", "delete", "Удаление пользователей"),
        
        # Напоминания
        ("reminders", "create", "Создание напоминаний"),
        ("reminders", "read", "Просмотр напоминаний"),
        ("reminders", "update", "Редактирование напоминаний"),
        ("reminders", "delete", "Удаление напоминаний"),
        
        # Роли
        ("roles", "create", "Создание ролей"),
        ("roles", "read", "Просмотр ролей"),
        ("roles", "update", "Редактирование ролей"),
        ("roles", "delete", "Удаление ролей"),
        
        # Права
        ("permissions", "read", "Просмотр прав доступа"),
        ("permissions", "assign", "Назначение прав ролям"),
        
        # Логи
        ("audit_logs", "read", "Просмотр логов аудита"),
    ]

    created_count = 0
    for resource, action, description in permissions_data:
        perm_name = f"{resource}:{action}"

        # Проверка на существование прав
        result = await session.execute(
            select(Permission).where(Permission.name == perm_name)
        )

        if not result.scalar_one_or_none():
            permission = Permission(
                name = perm_name,
                resource = resource,
                action = action,
                description = description
            )

            session.add(permission)
            created_count += 1
        
        await session.commit()
        print(f"✅ Создано записей прав - {created_count}")

async def create_roles(session: AsyncSession):
    ''' Добавление ролей '''
    print("\n👥 Создание ролей...")

    # Получаем все права
    result = await session.execute(select(Permission))
    all_permissions = result.scalars().all()

    # admin_role, manager_role, user_role
    admin_role = Role(
        name="ADMIN",
        description = "Полный доступ ко всем функциям системы",
        is_system = True
    )

    manager_role = Role(
        name="MANAGER",
        description = "Управление пользователями и напоминаниями",
        is_system = True
    )

    user_role = Role(
        name="USER",
        description = "Базовые права для обычных пользователей",
        is_system = True
    )
    
    # У manager все права кроме редактирования Ролей и Прав
    manager_permissions = [p for p in all_permissions if not p.resource in [
        "roles", 
        "permissions"
    ]]
    
    # У пользователя только права на Напоминалку
    user_permissions = [p for p in all_permissions if p.name in [
        "reminders:create", "reminders:read", "reminders:update", "reminders:delete"
    ]]

    admin_role.permissions = all_permissions
    manager_role.permissions = manager_permissions
    user_role.permissions = user_permissions

    session.add(admin_role)
    session.add(manager_role)
    session.add(user_role)

    await session.commit()
    print("✅ Созданы роли: admin, manager, user")

async def create_first_admin(session: AsyncSession):
    """Создает единственного администратора"""
    print("\n👤 Создание администратора...")

    result = await session.execute(
        select(User).join(User.roles).where(Role.name == "ADMIN")
    )

    # Если админ уже есть
    if result.scalar_one_or_none():
        print("ℹ️  Администратор уже существует")
        return

    # Получаем роль
    result = await session.execute(
        select(Role).where(Role.name == "ADMIN")
    )

    role_admin = result.scalar_one()

    # Создаём админа
    hashed_password = pass256.hash("admin")
    # print(f"PBKDF2: {hashed_password}")
    admin = User(
        username = "Admin",
        email = "admin@example.com",
        hashed_password = hashed_password,
        is_active = True
    )
    admin.roles.append(role_admin)
    session.add(admin)
    await session.commit()

    print("✅ Создан администратор:")
    print("   Логин: Admin")
    print("   Пароль: admin")
    print("   ⚠️  НЕ ЗАБУДЬ СМЕНИТЬ ПАРОЛЬ В ПРОДАКШЕНЕ!")

async def create_first_user(session: AsyncSession):
    """Создает демо-данные для тестирования (пользователь)"""
    print("\n📝 Создание демо-данных...")

    # Получаем роль пользователя
    result = await session.execute(
        select(Role).where(Role.name == "USER")
    )
    role_user = result.scalar_one()

    # Хешируем пароль
    hashed_pass = pass256.hash("user")

    # Создание пользователя
    user = User(
        username = "User",
        email = "user@example.ru",
        hashed_password = hashed_pass,
        is_active = True,
        telegram_chat_id = "123456789"  # для теста
    )

    user.roles.append(role_user)
    session.add(user)
    await session.commit()

    print("✅ Создан пользователь:")
    print("   Логин: User")
    print("   Пароль: user")

async def main():
    print("=" * 50)
    print("🚀 УСТАНОВКА REMINDER BOT")
    print("=" * 50)

    await init_database()
    async with AssyncSessionLocal() as session:
        await create_permission(session)
        await create_roles(session)
        await create_first_admin(session)
        await create_first_user(session)

    print("\n" + "=" * 50)
    print("✅ УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())