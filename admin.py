from fastapi import HTTPException
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from auth.models import User
from tasks.models import Task, Comment, TaskFile, EmailNotification
from sqladmin import ModelView


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


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username]


class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.headline]


class CommentAdmin(ModelView, model=Comment):
    column_list = [Comment.id, Comment.text]


class TaskFileAdmin(ModelView, model=TaskFile):
    column_list = [TaskFile.id, TaskFile.name]
