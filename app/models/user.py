from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True)  # Telegram user_id
    vk_user_id = Column(Integer, nullable=True)
    vk_access_token = Column(Text, nullable=True)  # Зашифрованный токен
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, vk_user_id={self.vk_user_id})>"