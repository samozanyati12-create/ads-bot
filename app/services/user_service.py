from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from app.core.security import encrypt_token, decrypt_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    async def get_user_by_telegram_id(session: AsyncSession, user_id: int) -> User:
        """Получение пользователя по Telegram ID"""
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(session: AsyncSession, user_id: int) -> User:
        """Создание нового пользователя"""
        user = User(user_id=user_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    @staticmethod
    async def get_or_create_user(session: AsyncSession, user_id: int) -> User:
        """Получение или создание пользователя"""
        user = await UserService.get_user_by_telegram_id(session, user_id)
        if not user:
            user = await UserService.create_user(session, user_id)
        return user
    
    @staticmethod
    async def update_vk_data(
        session: AsyncSession, 
        user_id: int, 
        vk_user_id: int, 
        access_token: str
    ) -> bool:
        """Обновление VK данных пользователя"""
        try:
            encrypted_token = encrypt_token(access_token)
            
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(
                    vk_user_id=vk_user_id,
                    vk_access_token=encrypted_token,
                    last_seen=datetime.utcnow()
                )
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating VK data: {e}")
            await session.rollback()
            return False
    
    @staticmethod
    async def get_vk_token(session: AsyncSession, user_id: int) -> str:
        """Получение расшифрованного VK токена"""
        user = await UserService.get_user_by_telegram_id(session, user_id)
        if user and user.vk_access_token:
            return decrypt_token(user.vk_access_token)
        return None

user_service = UserService()