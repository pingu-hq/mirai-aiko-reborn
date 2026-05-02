from fastapi import APIRouter, status, HTTPException, Response, Request
from pydantic import BaseModel
from src.core.security import SecurityAuth
from src.data_storage.mongo_db_data_store import MongoDbDataStore
import asyncio



router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

class Login(BaseModel):
    email: str
    password: str

class SignUp(Login):
    name: str

@router.post("/login", status_code=status.HTTP_200_OK)
async def login_endpoint(login: Login, resp: Response):
    mongo_db = MongoDbDataStore()
    user_info = await mongo_db.get_user_by_email(login.email)
    hashed_password = user_info.get("password")

    sa = SecurityAuth()
    validity = await sa.login_with_cookie(
        user=login.email,
        password=login.password,
        hashed_password=hashed_password,
        resp=resp
    )
    if not validity:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect username or password")
    return {"status":"ok"}


@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up_endpoint(sign_user: SignUp):
    try:
        mongo_db = MongoDbDataStore()
        user_id = await mongo_db.create_user(
            email=sign_user.email,
            name=sign_user.name,
            password=sign_user.password
        )
        return {"status":"ok", "user_id":user_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

@router.get("/me", status_code=status.HTTP_202_ACCEPTED)
def check_cookie_good(resp: Response, req: Request):
    sa = SecurityAuth()
    _id = sa.get_cookie_id(req, resp)
    return {"_id":_id}

@router.get("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_endpoint(resp: Response, req: Request):
    sa = SecurityAuth()
    if not sa.logout(req, resp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
