from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    ForeignKey, Text, Index, Table
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('assigned_by', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
)

role_permission = Table(
    'role_permission',
    Base.metadata,
    Column('role_id',       Integer, ForeignKey('roles.id',       ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
)

class User(Base):
    ''' 
    Обязательные поля:
        username -> String
        email -> String
        hashed_password -> String
        is_active -> Boolean

    Например:
        username = "User",
        email = "user@example.com",
        hashed_password = hashed_password,
        is_active = True
    '''
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    telegram_chat_id = Column(String(50), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    reminders = relationship(
        "Reminder", 
        back_populates="owner", 
        cascade="all, delete-orphan",
        lazy="selectin"  # Оптимизация для асинхронной загрузки
    )

    notification_logs = relationship(
        "NotificationLog", 
        back_populates="user",
        cascade="all, delete-orphan"
    )

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
        foreign_keys=[user_roles.c.user_id, user_roles.c.role_id]
    )

    @property
    def get_all_permissions(self)->set:
        ''' Возвращает множество всех прав пользователя (из всех его ролей)'''
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.name)
        return perms
    
    @property
    def is_admin(self):
        ''' Проверяет, является ли пользователь Админом '''
        return any(role.name == "ADMIN" for role in self.roles)

    @property
    def has_permission(self, perm_name:str)->bool:
        ''' Проверяет, есть ли у пользователь конкретная роль '''
        return perm_name in self.get_all_permissions()

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False) # Системные роли нельзя удалить
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        foreign_keys=[user_roles.c.role_id, user_roles.c.user_id]
    )
    
    permissions = relationship(
        "Permission",
        secondary=role_permission,
        back_populates="roles",
        lazy="selectin"
    )

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) # например: "reminders:create"
    resource = Column(String(255), nullable=False)  # "reminders", "users", "roles"
    action   = Column(String(255), nullable=False)  # "create", "read", "update", "delete"
    description = Column(String(255), nullable=True)

    # Связи
    roles = relationship(
        "Role",
        secondary=role_permission,
        back_populates="permissions"
    )

    @property
    def get_permission(self):
        ''' Возвращает полное название в виде resource:action '''
        return f"{self.resource}:{self.action}"

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(500), nullable=False)
    remind_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_sent = Column(Boolean, default=False, index=True)
    is_cancelled = Column(Boolean, default=False)  # Возможность отмены
    repeat_daily = Column(Boolean, default=False)   # Повтор каждый день
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Внешний ключ
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Связи
    owner = relationship(
        "User", 
        back_populates="reminders"
    )

    notification_logs = relationship(
        "NotificationLog", 
        back_populates="reminder",
        cascade="all, delete-orphan"
    )

    #__table_args__ = (Index('ix_reminders_active', 'remind_at', 'is_sent', 'is_cancelled'),)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    telegram_message_id = Column(String(50), nullable=True)

    reminder = relationship("Reminder", back_populates="notification_logs")
    user = relationship("User", back_populates="notification_logs")

    #__table_args__ = (Index('ix_logs_user_status', 'user_id', 'status'),)

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    revoked_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

class AuditLog(Base):
    """Лог действий пользователей для безопасности"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action  = Column(String(100), nullable=False) # "user:login", "reminder:create"
    resource_type = Column(String(45), nullable=True) # "user", "reminder"
    resource_id   = Column(Integer, nullable=True)
    ip_addres  = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(Text, nullable=True) # JSON с дополнительной информацией
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", foreign_keys=[user_id])