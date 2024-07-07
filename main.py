from fastapi import FastAPI
from tasks.router import router as task_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="JIRAlike"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return {"message": "Start page"}

app.include_router(task_router)