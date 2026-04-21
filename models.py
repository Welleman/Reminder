from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    telegram_chat_id = Column(String(50), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Для админки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
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
    owner = relationship("User", back_populates="reminders")
    notification_logs = relationship(
        "NotificationLog", 
        back_populates="reminder",
        cascade="all, delete-orphan"
    )