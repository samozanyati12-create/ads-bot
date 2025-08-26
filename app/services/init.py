"""
Сервисы для работы с внешними API и бизнес-логикой
"""

from .vk_service import vk_service, VKService
from .user_service import user_service, UserService

__all__ = [
    'vk_service',
    'VKService',
    'user_service', 
    'UserService'
]