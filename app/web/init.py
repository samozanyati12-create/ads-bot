"""
Веб-сервер для обработки callback'ов
"""

from .vk_callback import create_app, vk_callback_handler

__all__ = [
    'create_app',
    'vk_callback_handler'
]