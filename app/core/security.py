import base64
import hashlib
from app.core.config import settings

def encrypt_token(token: str) -> str:
    """Простое кодирование токена (для MVP)"""
    key = settings.SECRET_KEY.encode()
    encoded = base64.b64encode((token + key.hex()).encode())
    return encoded.decode()

def decrypt_token(encoded_token: str) -> str:
    """Простое декодирование токена"""
    try:
        key = settings.SECRET_KEY.encode()
        decoded = base64.b64decode(encoded_token.encode()).decode()
        return decoded.replace(key.hex(), '')
    except:
        return None