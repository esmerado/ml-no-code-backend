from pydantic import BaseModel


class TrainResponse(BaseModel):
    id: str
    email: str
    passwordHash: str
    emailVerified: bool
