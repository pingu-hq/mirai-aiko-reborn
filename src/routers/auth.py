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
async def login_endpoint(login: Login, resp: Response, request: Request):
    _error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized!")
    sa = SecurityAuth()
    if sa.check_current_user_logged_in(request=request):
        # print("ERROR IN EXISTING USER IN COOKIE")
        raise _error

    try:
        mongo_db = MongoDbDataStore()
        user_info_id, user_info_hash_pass = await mongo_db.get_id_and_password(login.email)
        if user_info_id is None or user_info_hash_pass is None:
            raise _error

        validity = await sa.login_with_cookie(
            user=user_info_id,
            password=login.password,
            hashed_password=user_info_hash_pass,
            resp=resp
        )
        if not validity:
            # print("ERROR IN VALIDITY OF LOGIN USER")
            raise _error
        return {"status":"ok"}

    except Exception as ex:
        print(str(ex))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up_endpoint(sign_user: SignUp):
    try:
        mongo_db = MongoDbDataStore()
        created_user = await mongo_db.create_user(
            email=sign_user.email,
            name=sign_user.name,
            password=sign_user.password
        )
        if not created_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)
        return {"status":"ok"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

@router.get("/me", status_code=status.HTTP_202_ACCEPTED)
def check_cookie_good(resp: Response, req: Request):
    sa = SecurityAuth()
    _id = sa.get_cookie_id(req, resp)
    return {"unique_identifier":_id}

@router.get("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_endpoint(request: Request):
    sa = SecurityAuth()
    sa.revocation_of_jti(request=request)
