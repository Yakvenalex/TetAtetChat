import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import SPartner, SMessge
from app.api.utils import generate_client_token, send_msg
from app.config import settings
from app.dao.dao import UserDAO
from app.dao.fastapi_dao_dep import get_session_with_commit, get_session_without_commit
from app.redis_config import get_redis_db

router = APIRouter(prefix="/api", tags=["АПИ"])


@router.post('/find-partner')
async def find_partner(
        user: SPartner,
        session: AsyncSession = Depends(get_session_without_commit),
        redis_client: Redis = Depends(get_redis_db)
):
    # Получаем полные данные пользователя
    full_user_data = await UserDAO(session).find_one_or_none_by_id(user.id)
    if not full_user_data:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user_nickname = full_user_data.nickname
    user_gender = full_user_data.gender
    user_age = full_user_data.age

    # Сначала проверяем, есть ли у пользователя уже существующие комнаты с двумя участниками
    user_rooms = await redis_client.smembers(f"user_rooms:{user.id}")

    for room_key in user_rooms:
        room_data = await redis_client.get(room_key)
        if room_data:
            room_info = json.loads(room_data)
            participants = room_info.get("participants", [])
            if len(participants) == 2 and any(participant["id"] == user.id for participant in participants):
                # Если комната с двумя участниками найдена, возвращаем статус "matched"
                partner = next((p for p in participants if p["id"] != user.id), None)
                user_token = await generate_client_token(user.id, settings.SECRET_KEY)
                if partner:
                    return {
                        "status": "matched",
                        "room_key": room_key,
                        "partner": {
                            "id": partner["id"],
                            "nickname": partner["nickname"]
                        },
                        "token": user_token,
                        "sender": user_nickname,
                        "user_id": user.id
                    }

    # Если подходящей комнаты не нашлось, продолжаем поиск или создание новой комнаты
    # Формируем базовый ключ для поиска комнаты (только по полу)
    room_base_key = f"chat_room:{user_gender}_*"

    # Получаем список всех комнат, соответствующих полу
    all_keys = await redis_client.keys(room_base_key)

    # Проходимся по списку комнат и ищем подходящую
    for key in all_keys:
        room_data = await redis_client.get(key)
        if not room_data:
            continue

        room_info = json.loads(room_data)
        participants = room_info.get("participants", [])

        # Если в комнате уже 2 участника, пропускаем её
        if len(participants) >= 2:
            continue

        # Если в комнате уже есть текущий пользователь, пропускаем её
        if any(participant["id"] == user.id for participant in participants):
            continue

        # Получаем данные о пользователе в комнате
        room_owner = participants[0]
        room_owner_gender = room_owner.get("gender", "any")
        room_owner_looking_for = room_owner.get("looking_for_gender", "any")
        room_owner_age_from = room_owner.get("looking_for_age_from", 0)
        room_owner_age_to = room_owner.get("looking_for_age_to", 999)

        # Проверяем соответствие по полу
        user_gender_preference_match = user.gender == "any" or user.gender == room_owner_gender
        room_owner_gender_preference_match = room_owner_looking_for == "any" or room_owner_looking_for == user_gender
        gender_match = user_gender_preference_match and room_owner_gender_preference_match

        # Проверяем пересечение диапазонов возрастов
        user_age_range = range(user.age_from, user.age_to + 1)
        room_owner_age_range = range(room_owner_age_from, room_owner_age_to + 1)
        age_match = bool(set(user_age_range).intersection(room_owner_age_range))

        # Если оба условия выполняются, найдено соответствие
        if gender_match and age_match:
            # Генерируем JWT токен для текущего пользователя
            user_token = await generate_client_token(user.id, settings.SECRET_KEY)

            # Добавляем пользователя в существующую комнату
            participants.append({
                "id": user.id,
                "nickname": user_nickname,
                "gender": user_gender,
                "age": user_age,
                "looking_for_gender": user.gender,
                "looking_for_age_from": user.age_from,
                "looking_for_age_to": user.age_to,
                "token": user_token
            })

            # Обновляем данные о комнате
            room_info["participants"] = participants
            await redis_client.set(key, json.dumps(room_info))

            # Получаем данные о партнере (без токена)
            partner = {
                "id": room_owner["id"],
                "nickname": room_owner["nickname"]
            }

            # Связываем комнату с обоими пользователями
            room_key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            await redis_client.sadd(f"user_rooms:{user.id}", room_key_str)
            await redis_client.sadd(f"user_rooms:{partner['id']}", room_key_str)

            return {
                "status": "matched",
                "room_key": room_key_str,
                "partner": partner,
                "token": user_token,
                "sender": user_nickname,
                "user_id": user.id
            }

    # Если подходящей комнаты не нашлось, создаем новую с уникальным идентификатором
    new_room_key = f"chat_room:{user_gender}_{uuid.uuid4().hex[:8]}"

    # Генерируем JWT токен для пользователя
    user_token = await generate_client_token(user.id, settings.SECRET_KEY)

    new_room_data = {
        "participants": [
            {
                "id": user.id,
                "nickname": user_nickname,
                "gender": user_gender,
                "age": user_age,
                "looking_for_gender": user.gender,
                "looking_for_age_from": user.age_from,
                "looking_for_age_to": user.age_to,
                "token": user_token
            }
        ],
        "created_at": datetime.now().isoformat()
    }

    # Сохраняем информацию о комнате
    await redis_client.set(new_room_key, json.dumps(new_room_data))
    # Устанавливаем TTL для записи (например, 60 минут)
    # await redis_client.expire(new_room_key, 3600)

    return {
        "status": "waiting",
        "room_key": new_room_key,
        "partner": None,
        "message": "Ожидаем подходящего партнера",
        "token": user_token,
        "sender": user_nickname,
        "user_id": user.id
    }


@router.get('/room-status')
async def room_status(
        key: str,
        user_id: int,
        redis_client: Redis = Depends(get_redis_db)
):
    # Получаем данные о комнате из Redis
    room_data = await redis_client.get(key)
    if not room_data:
        print(f"STATUS: Комната не найдена!")
        raise HTTPException(status_code=404, detail="Комната не найдена")

    room_info = json.loads(room_data)
    participants = room_info.get("participants", [])

    # Если в комнате 2 участника, значит партнер найден
    if len(participants) == 2:
        # Находим партнера (не текущего пользователя)
        partner = next(
            (participant for participant in participants if participant["id"] != user_id),
            None
        )
        if not partner:
            raise HTTPException(status_code=500, detail="Ошибка при поиске партнера")

        print(f"STATUS: matched!")
        return {
            "status": "matched",
            "room_key": key,
            "partner": {
                "id": partner["id"],
                "nickname": partner["nickname"]
            }
        }

    # Если в комнате только один участник, значит ожидание
    elif len(participants) == 1:
        print(f"STATUS: waiting!")
        return {
            "room_key": key,
            "status": "waiting",
            "message": "Ожидаем подходящего партнера"
        }

    # Если комната пуста или участников больше 2, значит комната закрыта
    else:
        print(f"STATUS: closed!")
        return {
            "room_key": key,
            "status": "closed",
            "message": "Комната закрыта"
        }


@router.post("/clear_room/{room_id}")
async def clear_room(room_id: str, redis_client: Redis = Depends(get_redis_db)):
    # Асинхронно удаляем ключ, связанный с room_id
    print(room_id)
    await redis_client.unlink(room_id)
    return {"message": f"Ключ для комнаты {room_id} удален"}


@router.post("/clear_redis")
async def clear_redis(redis_client: Redis = Depends(get_redis_db)):
    # Очищаем все ключи из Redis
    await redis_client.flushdb()
    return {"message": "Redis база данных очищена"}


@router.post("/send-msg/{room_id}")
async def vote(room_id: str, msg: SMessge):
    data = msg.model_dump()
    is_sent = await send_msg(
        data=data,
        channel_name=room_id
    )
    return {"status": "ok" if is_sent else "failed"}