import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.core.config import settings
from app.core.database import create_tables, close_db
from app.bot.handlers.auth import router
from app.web.vk_callback import create_app
from app.services.vk_service import vk_service

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def create_combined_app():
    """Создание объединенного приложения с ботом и веб-сервером"""
    
    # Создание бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)
    
    # Создание веб-приложения
    app = create_app()
    
    # Настройка webhook для бота (для продакшена)
    if settings.DEBUG:
        # В режиме разработки - polling
        return bot, dp, app
    else:
        # В продакшене - webhook
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        return bot, dp, app

async def main():
    try:
        # Инициализация БД
        await create_tables()
        logger.info("База данных инициализирована")
        
        # Создание приложения
        bot, dp, app = await create_combined_app()
        
        if settings.DEBUG:
            # Режим разработки - запуск polling + веб-сервер
            logger.info("Запуск в режиме разработки (polling)")
            
            # Запуск веб-сервера в отдельной задаче
            async def run_web_server():
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, 'localhost', 8000)
                await site.start()
                logger.info("Веб-сервер запущен на http://localhost:8000")
            
            # Создаем задачи
            web_task = asyncio.create_task(run_web_server())
            bot_task = asyncio.create_task(dp.start_polling(bot))
            
            # Ждем выполнения обеих задач
            await asyncio.gather(web_task, bot_task)
        else:
            # Режим продакшена - только веб-сервер с webhook
            logger.info("Запуск в продакшн режиме (webhook)")
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', 8000)
            await site.start()
            
            # Устанавливаем webhook
            webhook_url = f"{settings.VK_REDIRECT_URI.replace('/vk-callback', '/webhook')}"
            await bot.set_webhook(webhook_url)
            logger.info(f"Webhook установлен: {webhook_url}")
            
            # Держим сервер запущенным
            await asyncio.Event().wait()
            
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
        raise
    finally:
        await vk_service.close()
        await close_db()
        logger.info("Приложение остановлено")

if __name__ == "__main__":
    asyncio.run(main())