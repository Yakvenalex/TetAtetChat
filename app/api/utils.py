import json
import time
import jwt
import httpx

from app.config import settings


async def send_msg(data: dict, channel_name: str) -> bool:
    # Сериализуем данные в JSON
    json_data = json.dumps(data)
    payload = {
        "method": "publish",
        "params": {"channel": channel_name, "data": json_data}
    }
    headers = {"X-API-Key": settings.CENTRIFUGO_API_KEY}
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(url=settings.CENTRIFUGO_URL,
                                     json=payload,
                                     headers=headers)
        return response.status_code == 200


async def generate_client_token(user_id, secret_key):
    # Устанавливаем время жизни токена (например, 60 минут)
    exp = int(time.time()) + 60 * 60  # Время истечения в секундах

    # Создаем полезную нагрузку токена
    payload = {
        "sub": str(user_id),  # Идентификатор пользователя
        "exp": exp  # Время истечения
    }

    # Генерируем токен с использованием HMAC SHA-256
    return jwt.encode(payload, secret_key, algorithm="HS256")
