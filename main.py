from fastapi import FastAPI, Depends
from tasks.router import router as task_router
from fastapi.staticfiles import StaticFiles
from auth.user_manager import auth_backend, current_active_user, fastapi_users
from auth.models import User
from auth.schemas import UserCreate, UserRead, UserUpdate

app = FastAPI(
    title="JIRAlike"
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def get_index():
    return {"message": "Start page"}


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.username}!"}

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
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


