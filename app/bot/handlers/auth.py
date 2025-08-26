from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from app.core.config import settings
from app.services.user_service import user_service
from app.services.vk_service import vk_service
from app.core.database import async_session
import urllib.parse
import logging

logger = logging.getLogger(__name__)
router = Router()

def generate_vk_auth_url(telegram_user_id: int) -> str:
    """Генерация URL для авторизации VK"""
    params = {
        'client_id': settings.VK_APP_ID,
        'redirect_uri': settings.VK_REDIRECT_URI,
        'scope': 'ads,offline',
        'response_type': 'code',
        'state': str(telegram_user_id)
    }
    
    base_url = "https://oauth.vk.com/authorize"
    return f"{base_url}?{urllib.parse.urlencode(params)}"

@router.message(Command("start"))
async def start_handler(message: Message):
    """Приветствие и начальная настройка"""
    # Создаем или получаем пользователя
    async with async_session() as session:
        await user_service.get_or_create_user(session, message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Подключить VK", callback_data="connect_vk")],
        [InlineKeyboardButton(text="📊 Проверить статус", callback_data="check_status")]
    ])
    
    await message.answer(
        "👋 <b>Добро пожаловать в VK Ads Analytics Bot!</b>\n\n"
        "🚀 Я помогу анализировать ваши рекламные кампании VK Ads\n"
        "📊 Предоставлю ежедневные отчеты и рекомендации\n\n"
        "Для начала подключите ваш VK аккаунт:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "connect_vk")
async def connect_vk_callback(callback: CallbackQuery):
    """Обработка кнопки подключения VK"""
    vk_auth_url = generate_vk_auth_url(callback.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Авторизоваться в VK", url=vk_auth_url)],
        [InlineKeyboardButton(text="🔄 Обновить статус", callback_data="check_status")]
    ])
    
    await callback.message.edit_text(
        "🔐 <b>Подключение VK Ads API:</b>\n\n"
        "1️⃣ Нажмите кнопку <b>\"Авторизоваться в VK\"</b>\n"
        "2️⃣ Разрешите доступ к рекламному аккаунту\n"
        "3️⃣ После успешной авторизации нажмите <b>\"Обновить статус\"</b>\n\n"
        "⚠️ <i>Потребуются права 'ads' для доступа к статистике</i>",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "check_status")
async def check_status_callback(callback: CallbackQuery):
    """Проверка статуса подключения"""
    async with async_session() as session:
        user = await user_service.get_user_by_telegram_id(session, callback.from_user.id)
        
        if not user or not user.vk_access_token:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Подключить VK", callback_data="connect_vk")]
            ])
            await callback.message.edit_text(
                "📊 <b>Статус подключения:</b>\n\n"
                "VK Ads: ❌ <i>Не подключен</i>\n"
                "Последняя синхронизация: -\n\n"
                "Подключите VK аккаунт для получения отчетов:",
                reply_markup=keyboard
            )
            return
        
        # Получаем токен и проверяем доступ
        access_token = await user_service.get_vk_token(session, callback.from_user.id)
        
        # Проверяем доступ к VK API
        user_info = await vk_service.get_user_info(access_token)
        
        if user_info:
            # Получаем рекламные аккаунты
            ad_accounts = await vk_service.get_ad_accounts(access_token)
            accounts_count = len(ad_accounts) if ad_accounts else 0
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📈 Получить отчет", callback_data="get_report")],
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="check_status")]
            ])
            
            await callback.message.edit_text(
                f"📊 <b>Статус подключения:</b>\n\n"
                f"VK Ads: ✅ <i>Подключен</i>\n"
                f"Пользователь: <b>{user_info.get('first_name', '')} {user_info.get('last_name', '')}</b>\n"
                f"Рекламных аккаунтов: <b>{accounts_count}</b>\n"
                f"Последняя активность: <i>{user.last_seen.strftime('%d.%m.%Y %H:%M') if user.last_seen else 'Неизвестно'}</i>\n\n"
                f"✅ Готов к получению отчетов!",
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Переподключить VK", callback_data="connect_vk")]
            ])
            await callback.message.edit_text(
                "📊 <b>Статус подключения:</b>\n\n"
                "VK Ads: ⚠️ <i>Ошибка доступа</i>\n\n"
                "Токен доступа истек или недействителен.\n"
                "Требуется повторная авторизация:",
                reply_markup=keyboard
            )

@router.callback_query(F.data == "get_report")
async def get_report_callback(callback: CallbackQuery):
    """Получение базового отчета"""
    await callback.message.edit_text(
        "📊 <b>Генерация отчета...</b>\n\n"
        "⏳ Получаем данные из VK Ads API...",
        reply_markup=None
    )
    
    try:
        async with async_session() as session:
            access_token = await user_service.get_vk_token(session, callback.from_user.id)
            
            if not access_token:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 Подключить VK", callback_data="connect_vk")]
                ])
                await callback.message.edit_text(
                    "❌ <b>Ошибка:</b> VK аккаунт не подключен",
                    reply_markup=keyboard
                )
                return
            
            # Получаем рекламные аккаунты
            ad_accounts = await vk_service.get_ad_accounts(access_token)
            
            if not ad_accounts:
                await callback.message.edit_text(
                    "📊 <b>Отчет по рекламным кампаниям</b>\n\n"
                    "ℹ️ Рекламные аккаунты не найдены или нет доступа.\n\n"
                    "Возможные причины:\n"
                    "• Нет активных рекламных аккаунтов\n"
                    "• Недостаточно прав доступа\n"
                    "• Аккаунты заблокированы",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 Обновить", callback_data="get_report")]
                    ])
                )
                return
            
            # Формируем отчет
            report_text = "📊 <b>Отчет по рекламным кампаниям</b>\n\n"
            
            for account in ad_accounts[:3]:  # Показываем только первые 3 аккаунта
                account_name = account.get('account_name', 'Без названия')
                account_id = account.get('account_id')
                account_status = account.get('account_status', 0)
                
                status_emoji = "✅" if account_status == 1 else "⏸️"
                
                report_text += f"{status_emoji} <b>{account_name}</b>\n"
                report_text += f"   ID: <code>{account_id}</code>\n"
                report_text += f"   Статус: {'Активен' if account_status == 1 else 'Приостановлен'}\n\n"
            
            if len(ad_accounts) > 3:
                report_text += f"... и еще {len(ad_accounts) - 3} аккаунтов\n\n"
            
            report_text += "📈 <i>Детальная статистика будет доступна в следующих версиях</i>"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить отчет", callback_data="get_report")],
                [InlineKeyboardButton(text="⚙️ Настройки", callback_data="check_status")]
            ])
            
            await callback.message.edit_text(report_text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await callback.message.edit_text(
            "❌ <b>Ошибка генерации отчета</b>\n\n"
            "Попробуйте позже или обратитесь в поддержку.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Повторить", callback_data="get_report")]
            ])
        )

@router.message(Command("status"))
async def status_handler(message: Message):
    """Команда проверки статуса"""
    await check_status_callback(CallbackQuery(
        id="status_cmd",
        from_user=message.from_user,
        chat_instance="status",
        message=message,
        data="check_status"
    ))

@router.message(Command("help"))
async def help_handler(message: Message):
    """Помощь по командам"""
    help_text = """
🔧 <b>Доступные команды:</b>

/start - Начать работу с ботом
/status - Проверить статус подключения  
/help - Показать эту справку

📊 <b>Функции:</b>
• Подключение VK Ads API
• Просмотр рекламных аккаунтов
• Базовые отчеты по кампаниям

🚀 <b>В разработке:</b>
• Детальная аналитика
• Автоматические отчеты  
• Рекомендации по оптимизации
    """
    
    await message.answer(help_text)