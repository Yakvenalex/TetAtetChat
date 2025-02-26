from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class NickSchema(BaseModel):
    nickname: str = Field(..., description="Никнейм пользователя")


class AgeSchema(BaseModel):
    age: int = Field(..., ge=0, description="Возраст пользователя")


class UserIdSchema(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор пользователя")


class UserSchema(NickSchema, AgeSchema, UserIdSchema):
    username: Optional[str] = Field(None, description="Имя пользователя")
    first_name: Optional[str] = Field(None, description="Имя")
    last_name: Optional[str] = Field(None, description="Фамилия")
    gender: str = Field(..., description="Пол пользователя")
    model_config = ConfigDict(from_attributes=True)
