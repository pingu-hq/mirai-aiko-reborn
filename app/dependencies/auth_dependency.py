from typing import Annotated

from fastapi import Depends, Request, Response

from app.services.http_cookie_service import HttpCookieAuthService

type HttpCookieAuthServiceDepends = Annotated[HttpCookieAuthService, Depends(get_http_cookie_auth_service)]


def get_http_cookie_auth_service(request: Request, response: Response) -> HttpCookieAuthService:
    return HttpCookieAuthService(request, response)