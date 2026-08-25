from pydantic import BaseModel, EmailStr


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str
    password: str





