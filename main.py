from fastapi import FastAPI
from tasks.router import router as task_router

app = FastAPI(
    title="JIRAlike"
)


@app.get("/")
async def get_index():
    return {"message": "Start page"}

app.include_router(task_router)