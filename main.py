from fastapi import FastAPI
from tasks.router import router as task_router
from fastapi.staticfiles import StaticFiles
from auth.user_manager import auth_backend, fastapi_users
from auth.schemas import UserCreate, UserRead
from starlette.middleware.sessions import SessionMiddleware
from database import engine
from sqladmin import Admin
from admin import authentication_backend, UserAdmin, TaskAdmin, CommentAdmin, TaskFileAdmin

app = FastAPI(
    title="JIRAlike"
)
app.add_middleware(SessionMiddleware, secret_key="some-random-string")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(task_router)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/users",
    tags=["users"]
)

admin = Admin(app, engine, authentication_backend=authentication_backend)

admin.add_view(UserAdmin)
admin.add_view(TaskAdmin)
admin.add_view(CommentAdmin)
admin.add_view(TaskFileAdmin)
