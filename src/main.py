from fastapi import FastAPI, Response, Request, status, HTTPException
from src.routers.auth import router as auth_router
from src.agentic_workflows.mirai_aiko_workflow import router as test_router
from src.core.security import SecurityAuth
import asyncio

app = FastAPI()

app.include_router(auth_router)
app.include_router(test_router)

@app.get("/hello-env-var")
async def hello_world():
    await asyncio.sleep(1)
    from src.core.local_config import settings
    return {"message": settings.hello_world}

# @app.get("/api")
# def me(request: Request, response: Response):
#     sa = SecurityAuth()
#     return {"id": sa.get_cookie_id(request, response)}
#
# @app.get("/api/logout", status_code=status.HTTP_204_NO_CONTENT)
# def logout_endpoint(resp: Response, req: Request):
#     sa = SecurityAuth()
#     if not sa.logout(req, resp):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
#


if __name__ == "__main__":
    import uvicorn
    print("RUNNING UVICORN")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )