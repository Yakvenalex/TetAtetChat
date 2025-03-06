from pydantic import BaseModel


class SPartner(BaseModel):
    id: int
    age_from: int = 0
    age_to: int = 999
    gender: str = "any"


class SMessge(BaseModel):
    sender: str
    user_id: int
    message: str
