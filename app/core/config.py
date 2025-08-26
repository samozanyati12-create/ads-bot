import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    
    # VK App
    VK_APP_ID: str = os.getenv("VK_APP_ID")
    VK_APP_SECRET: str = os.getenv("VK_APP_SECRET") 
    VK_REDIRECT_URI: str = os.getenv("VK_REDIRECT_URI")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    
    # Production settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API limits
    VK_API_REQUESTS_PER_SECOND: int = int(os.getenv("VK_API_REQUESTS_PER_SECOND", "3"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 час

    def validate(self):
        """Валидация обязательных настроек"""
        required = [
            "BOT_TOKEN", "VK_APP_ID", "VK_APP_SECRET", 
            "DATABASE_URL", "SECRET_KEY"
        ]
        for field in required:
            if not getattr(self, field):
                raise ValueError(f"Обязательная настройка {field} не задана")

settings = Settings()
settings.validate()