from fastapi import FastAPI
from tasks.router import router as task_router
from fastapi.staticfiles import StaticFiles
from auth.user_manager import auth_backend, fastapi_users
from auth.schemas import UserCreate, UserRead
from starlette.middleware.sessions import SessionMiddleware
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
