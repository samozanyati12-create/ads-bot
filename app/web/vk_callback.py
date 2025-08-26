from aiohttp import web, ClientSession
from aiohttp.web import Request, Response
import logging
from app.services.vk_service import vk_service
from app.services.user_service import user_service
from app.core.database import async_session

logger = logging.getLogger(__name__)

async def vk_callback_handler(request: Request) -> Response:
    """Обработчик VK OAuth callback"""
    try:
        # Получаем параметры из callback
        code = request.query.get('code')
        state = request.query.get('state')  # Telegram user_id
        error = request.query.get('error')
        
        if error:
            logger.error(f"VK OAuth error: {error}")
            return web.Response(
                text="Ошибка авторизации VK. Попробуйте еще раз.",
                status=400
            )
        
        if not code or not state:
            return web.Response(
                text="Неверные параметры авторизации.",
                status=400
            )
        
        telegram_user_id = int(state)
        
        # Обмениваем code на access_token
        token_data = await vk_service.exchange_code_for_token(code)
        if not token_data:
            return web.Response(
                text="Ошибка получения токена VK.",
                status=400
            )
        
        access_token = token_data['access_token']
        vk_user_id = token_data['user_id']
        
        # Сохраняем данные в БД
        async with async_session() as session:
            success = await user_service.update_vk_data(
                session, telegram_user_id, vk_user_id, access_token
            )
        
        if success:
            return web.Response(
                text="""
                ✅ Успешная авторизация!
                
                Ваш VK аккаунт подключен к боту.
                Теперь вы можете вернуться в Telegram и использовать команду /status
                """,
                content_type='text/plain; charset=utf-8'
            )
        else:
            return web.Response(
                text="Ошибка сохранения данных. Попробуйте еще раз.",
                status=500
            )
            
    except Exception as e:
        logger.error(f"VK callback error: {e}")
        return web.Response(
            text="Внутренняя ошибка сервера.",
            status=500
        )

# Создание веб-приложения
def create_app():
    app = web.Application()
    app.router.add_get('/vk-callback', vk_callback_handler)
    return app