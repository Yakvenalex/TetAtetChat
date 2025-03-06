import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any
from fastapi import HTTPException
from loguru import logger
from redis.asyncio import Redis
import jwt
import httpx
from app.config import settings
from app.dao.dao import UserDAO


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


async def create_new_room(user_id: int,
                          user_nickname: str,
                          user_gender: str,
                          user_age: int,
                          find_gender: str,
                          age_from: int,
                          age_to: int,
                          redis_client: Redis):
    new_room_key = f"{find_gender}_{uuid.uuid4().hex[:10]}"
    user_token = await generate_client_token(user_id, settings.SECRET_KEY)

    new_room_data = {"partners": [
        {
            "id": user_id,
            "nickname": user_nickname,
            "gender": user_gender,
            "age": user_age,
            "find_gender": find_gender,
            "age_from": age_from,
            "age_to": age_to,
            "token": user_token
        }
    ],
        "created_at": datetime.now().isoformat(),
        "room_key": new_room_key
    }

    await redis_client.set(new_room_key, json.dumps(new_room_data))
    return {
        "status": "waiting",
        "room_key": new_room_key,
        "message": "Ожидаем подходящего партнера",
        "token": user_token,
        "sender": user_nickname,
        "user_id": user_id,
    }


async def add_user_to_room(room, user_id, user_nickname, user_gender, user_age, find_gender, age_from, age_to,
                           redis_client):
    partners = room.get("partners", [])
    new_user_token = await generate_client_token(user_id, settings.SECRET_KEY)
    # Добавляем текущего пользователя в комнату
    new_partner = {
        "id": user_id,
        "nickname": user_nickname,
        "gender": user_gender,
        "age": user_age,
        "find_gender": find_gender,
        "age_from": age_from,
        "age_to": age_to,
        "token": new_user_token
    }
    partners.append(new_partner)

    # Обновляем данные комнаты в Redis
    room_key = room.get("room_key")
    await redis_client.set(room_key, json.dumps(room))

    # Возвращаем статус "matched"
    return {
        "status": "matched",
        "room_key": room_key,
        "message": "Партнер найден",
        "token": new_user_token,
        "sender": user_nickname,
        "user_id": user_id
    }


async def refund_partner(room_key, user_id, user_nickname, status="matched", message="Партнер найден"):
    new_user_token = await generate_client_token(user_id, settings.SECRET_KEY)
    return {
        "status": status,
        "room_key": room_key,
        "message": message,
        "token": new_user_token,
        "sender": user_nickname,
        "user_id": user_id
    }


async def get_user_info(session, user_id):
    full_user_data = await UserDAO(session).find_one_or_none_by_id(user_id)
    if not full_user_data:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"nickname": full_user_data.nickname, "gender": full_user_data.gender, "age": full_user_data.age}


async def get_all_rooms_gender(redis_client: Redis) -> List[Dict[str, Any]]:
    """
    Возвращает все данные по ключам.

    :param redis_client: Клиент Redis.
    :return: Список словарей с данными комнат.
    """
    all_keys = await redis_client.keys()
    rooms_data = []

    if all_keys:
        # Используем mget для получения значений по всем ключам одновременно
        values = await redis_client.mget(all_keys)

        for key, value in zip(all_keys, values):
            if value:
                try:
                    room_dict = json.loads(value)
                    rooms_data.append(room_dict)
                except json.JSONDecodeError:
                    logger.error(f"Ошибка декодирования JSON для ключа {key}")

    return rooms_data


def is_match(
        user_gender: str,
        user_find_gender: str,
        user_age: int,
        user_age_from: int,
        user_age_to: int,
        partner_gender: str,
        partner_find_gender: str,
        partner_age: int,
        partner_age_from: int,
        partner_age_to: int
) -> bool:
    """
    Проверяет, подходят ли пользователь и партнер друг другу по полу и возрасту.

    :param user_gender: Пол текущего пользователя.
    :param user_find_gender: Пол, который ищет текущий пользователь.
    :param user_age: Возраст текущего пользователя.
    :param user_age_from: Минимальный возраст, который ищет текущий пользователь.
    :param user_age_to: Максимальный возраст, который ищет текущий пользователь.
    :param partner_gender: Пол партнера.
    :param partner_find_gender: Пол, который ищет партнер.
    :param partner_age: Возраст партнера.
    :param partner_age_from: Минимальный возраст, который ищет партнер.
    :param partner_age_to: Максимальный возраст, который ищет партнер.
    :return: True, если пользователь и партнер подходят друг другу, иначе False.
    """
    # Проверка по полу
    is_gender_match = (
            (partner_find_gender == "any" or partner_find_gender == user_gender) and
            (user_find_gender == "any" or user_find_gender == partner_gender)  # Текущий пользователь ищет партнера
    )

    # Проверка по возрасту
    is_age_match = (
            (partner_age_from <= user_age <= partner_age_to) and  # Возраст пользователя подходит партнеру
            (user_age_from <= partner_age <= user_age_to)  # Возраст партнера подходит пользователю
    )

    # Возвращаем True, если оба условия выполнены
    return is_gender_match and is_age_match
