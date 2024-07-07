import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from database import get_async_session
from . import models, schemas

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/", response_model=List[schemas.TaskRel])
async def get_tasks(session: AsyncSession = Depends(get_async_session)):
    query = (
        select(models.Task)
        .options(selectinload(models.Task.comments))
        .options(joinedload(models.Task.file))
    )
    result = await session.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=schemas.TaskRel)
async def get_one_task(task_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
        # query = select(models.Task).filter(models.Task.id == task_id)
        query = (
            select(models.Task)
            .filter_by(id=task_id)
            .options(selectinload(models.Task.comments))
            .options(joinedload(models.Task.file))
        )
        result = await session.execute(query)
        task = result.scalars().one()
        return task
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Item not found")


@router.post("/")
async def add_task(new_task: schemas.TaskAdd, session: AsyncSession = Depends(get_async_session)):
    stmt = insert(models.Task).values(**new_task.dict())
    await session.execute(stmt)
    await session.commit()
    return {"status": "OK"}


@router.post("/{task_id}/comment")
async def add_comment(new_comment: schemas.CommentAdd, session: AsyncSession = Depends(get_async_session)):
    stmt = insert(models.Comment).values(**new_comment.dict())
    await session.execute(stmt)
    await session.commit()
    return {"status": "OK"}


@router.get("/{task_id}/comments", response_model=List[schemas.Comment])
async def get_comments_from_specified_task(task_id: int, session: AsyncSession = Depends(get_async_session)):
    query = (
        select(models.Comment)
        .filter_by(task_id=task_id)
        )
    result = await session.execute(query)
    comments = result.scalars().all()
    return comments


@router.post("/upload", summary="Upload your Post picture")
async def upload(task_id: int, session: AsyncSession = Depends(get_async_session), file: UploadFile = File(...)):
    with open(f"static/taskfiles/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    mimetype = file.content_type
    name = file.filename

    taskfile = models.TaskFile(name=name, minetype=mimetype, task_id=task_id)
    session.add(taskfile)
    await session.commit()
    return f"{name} has been Successfully Uploaded"
