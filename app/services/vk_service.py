import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class VKService:
    def __init__(self):
        self.base_url = "https://api.vk.com/method"
        self.api_version = "5.131"
        self.session = None
    
    async def get_session(self):
        """Получение HTTP сессии"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Обмен code на access_token"""
        url = "https://oauth.vk.com/access_token"
        params = {
            'client_id': settings.VK_APP_ID,
            'client_secret': settings.VK_APP_SECRET,
            'redirect_uri': settings.VK_REDIRECT_URI,
            'code': code
        }
        
        session = await self.get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'access_token' in data:
                        return data
                    else:
                        logger.error(f"VK OAuth error: {data}")
                        return None
                else:
                    logger.error(f"VK OAuth HTTP error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"VK OAuth request error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Получение информации о пользователе"""
        url = f"{self.base_url}/users.get"
        params = {
            'access_token': access_token,
            'v': self.api_version
        }
        
        session = await self.get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'response' in data:
                        return data['response'][0]
                    else:
                        logger.error(f"VK API error: {data}")
                        return None
        except Exception as e:
            logger.error(f"VK API request error: {e}")
            return None
    
    async def get_ad_accounts(self, access_token: str) -> Optional[list]:
        """Получение списка рекламных аккаунтов"""
        url = f"{self.base_url}/ads.getAccounts"
        params = {
            'access_token': access_token,
            'v': self.api_version
        }
        
        # Ограничение скорости запросов
        await asyncio.sleep(1.0 / settings.VK_API_REQUESTS_PER_SECOND)
        
        session = await self.get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'response' in data:
                        return data['response']
                    else:
                        logger.error(f"VK Ads API error: {data}")
                        return None
        except Exception as e:
            logger.error(f"VK Ads API request error: {e}")
            return None

# Глобальный экземпляр сервиса
vk_service = VKService()