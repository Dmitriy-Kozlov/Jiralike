from fastapi import HTTPException
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request


class AdminAuth(AuthenticationBackend):
    async def authenticate(self, request: Request) -> bool:
        token = request.cookies.get('bonds')
        from auth.user_manager import is_admin_token, get_jwt_strategy
        if not token or not is_admin_token(request,
                                           token,
                                           get_jwt_strategy().secret,
                                           get_jwt_strategy().token_audience,
                                           get_jwt_strategy().algorithm):
            raise HTTPException(status_code=403, detail="Not authorized to administrate")
        return True


authentication_backend = AdminAuth(secret_key="supersecret")
