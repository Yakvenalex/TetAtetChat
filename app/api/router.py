import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas import SPartner, SMessge
from app.api.utils import (
    send_msg,
    create_new_room,
    get_user_info,
    get_all_rooms_gender,
    add_user_to_room,
    refund_partner,
    is_match,
)
from app.dao.fastapi_dao_dep import get_session_without_commit
from app.redis_dao.custom_redis import CustomRedis
from app.redis_dao.manager import get_redis

router = APIRouter(prefix="/api", tags=["АПИ"])


@router.post("/find-partner")
async def find_partner(
    user: SPartner,
    session: AsyncSession = Depends(get_session_without_commit),
    redis_client: CustomRedis = Depends(get_redis),
):
    # Получаем полные данные пользователя
    user_data = await get_user_info(session, user.id)

    # Данные пользователя
    user_nickname = user_data["nickname"]
    user_gender = user_data["gender"]
    user_age = user_data["age"]

    # Данные для поиска
    age_from = user.age_from
    age_to = user.age_to
    find_gender = user.gender

    # Получаем все комнаты для искомого пола
    all_rooms = await get_all_rooms_gender(redis_client)

    if len(all_rooms) == 0:
        # Если нет подходящих комнат, создаем новую
        return await create_new_room(
            user_id=user.id,
            user_nickname=user_nickname,
            user_gender=user_gender,
            user_age=user_age,
            find_gender=user.gender,
            age_from=age_from,
            age_to=age_to,
            redis_client=redis_client,
        )
    else:
        # Ищем подходящую комнату
        for room in all_rooms:
            partners = room.get("partners", [])
            if len(partners) == 1:
                partner_data = partners[0]
                if partner_data["id"] != user.id:
                    if is_match(
                        user_gender=user_gender,
                        user_find_gender=find_gender,
                        user_age=user_age,
                        user_age_from=age_from,
                        user_age_to=age_to,
                        partner_gender=partner_data.get("gender"),
                        partner_find_gender=partner_data.get("find_gender"),
                        partner_age=partner_data.get("age"),
                        partner_age_from=partner_data.get("age_from"),
                        partner_age_to=partner_data.get("age_to"),
                    ):
                        return await add_user_to_room(
                            room,
                            user.id,
                            user_nickname,
                            user_gender,
                            user_age,
                            find_gender,
                            age_from,
                            age_to,
                            redis_client,
                        )
                else:
                    return await refund_partner(
                        room.get("room_key"),
                        user.id,
                        user_nickname,
                        status="waiting",
                        message="Ожидаем подходящего партнера",
                    )
            elif len(partners) == 2:
                if partners[0]["id"] == user.id or partners[1]["id"] == user.id:
                    return await refund_partner(
                        room.get("room_key"), user.id, user_nickname
                    )
            continue
        # Если подходящая комната не найдена, создаем новую
        return await create_new_room(
            user_id=user.id,
            user_nickname=user_nickname,
            user_gender=user_gender,
            user_age=user_age,
            find_gender=user.gender,
            age_from=age_from,
            age_to=age_to,
            redis_client=redis_client,
        )


@router.get("/room-status")
async def room_status(
    key: str, user_id: int, redis_client: CustomRedis = Depends(get_redis)
):
    # Получаем данные о комнате из Redis
    room_data = await redis_client.get(key)
    if not room_data:
        raise HTTPException(status_code=404, detail="Комната не найдена")

    room_info = json.loads(room_data)
    participants = room_info.get("partners", [])

    # Если в комнате 2 участника, значит партнер найден
    if len(participants) == 2:
        # Находим партнера (не текущего пользователя)
        partner = next(
            (
                participant
                for participant in participants
                if participant["id"] != user_id
            ),
            None,
        )
        if not partner:
            raise HTTPException(status_code=500, detail="Ошибка при поиске партнера")

        return {
            "status": "matched",
            "room_key": key,
            "partner": {"id": partner["id"], "nickname": partner["nickname"]},
        }

    # Если в комнате только один участник, значит ожидание
    elif len(participants) == 1:
        print(f"STATUS: waiting!")
        return {
            "room_key": key,
            "status": "waiting",
            "message": "Ожидаем подходящего партнера",
        }

    # Если комната пуста или участников больше 2, значит комната закрыта
    else:
        print(f"STATUS: closed!")
        return {"room_key": key, "status": "closed", "message": "Комната закрыта"}


@router.post("/clear_room/{room_id}")
async def clear_room(room_id: str, redis_client: CustomRedis = Depends(get_redis)):
    # Асинхронно удаляем ключ, связанный с room_id
    await redis_client.unlink(room_id)
    return {"status": "ok", "message": f"Ключ для комнаты {room_id} удален"}


@router.post("/clear_redis")
async def clear_redis(redis_client: CustomRedis = Depends(get_redis)):
    # Очищаем все ключи из Redis
    await redis_client.flushdb()
    return {"message": "Redis база данных очищена"}


@router.post("/send-msg/{room_id}")
async def vote(room_id: str, msg: SMessge):
    data = msg.model_dump()
    is_sent = await send_msg(data=data, channel_name=room_id)
    return {"status": "ok" if is_sent else "failed"}
