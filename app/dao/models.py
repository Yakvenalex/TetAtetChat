from sqlalchemy import BigInteger
from app.dao.database import Base
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None]
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    nickname: Mapped[str]
    gender: Mapped[str]
    age: Mapped[int]
