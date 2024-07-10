import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from auth.user_manager import current_active_user
from database import get_async_session
from .models import Task, Comment, TaskFile, EmailNotification
from .schemas import TaskRel, TaskAdd, CommentAdd, CommentRead, CommentRel
from auth.models import User

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/", response_model=List[TaskRel])
async def get_tasks(
        task_filter: str = None,
        session: AsyncSession = Depends(get_async_session),
        ):
    query = (
        select(Task)
        .options(joinedload(Task.file))
        .options(joinedload(Task.owner))
        .options(selectinload(Task.comments))
    )
    if task_filter:
        query = query.filter(Task.headline.icontains(task_filter))
    result = await session.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/my_tasks", response_model=List[TaskRel], )
async def get_tasks(
        task_filter: str = None,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)
        ):
    query = (
        select(Task).filter_by(owner=user)
        .options(selectinload(Task.comments))
        .options(joinedload(Task.file))
        .options(joinedload(Task.owner))
    )
    if task_filter:
        query = query.filter(Task.headline.icontains(task_filter))
    result = await session.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskRel)
async def get_one_task(task_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
        # query = select(models.Task).filter(models.Task.id == task_id)
        query = (
            select(Task)
            .filter_by(id=task_id)
            .options(selectinload(Task.comments))
            .options(joinedload(Task.file))
            .options(joinedload(Task.owner))
        )
        result = await session.execute(query)
        task = result.scalars().one()
        return task
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Item not found")


@router.post("/")
async def add_task(
        new_task: TaskAdd,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)):
    new_task_db = Task(**new_task.dict(), owner=user)
    # stmt = insert(models.Task).values(**new_task.dict())
    # await session.execute(stmt)
    session.add(new_task_db)
    await session.flush()
    new_notification = EmailNotification(email=user.email, task_id=new_task_db.id)
    session.add(new_notification)
    await session.commit()
    return {"status": "OK"}


@router.post("/{task_id}/comment")
async def add_comment(
        new_comment: CommentAdd,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)):
    new_comment_db = Comment(**new_comment.dict(), owner=user)
    query = select(EmailNotification).filter_by(task_id=new_comment_db.task_id)
    result_emails = await session.execute(query)
    if user.email not in (row.email for row in result_emails.scalars().all()):
        new_notification = EmailNotification(email=user.email, task_id=new_comment_db.task_id)
        session.add(new_notification)
    session.add(new_comment_db)
    # stmt = insert(models.Comment).values(**new_comment.dict())
    # await session.execute(stmt)
    await session.commit()
    return {"status": "OK"}


@router.get("/{task_id}/comments", response_model=List[CommentRel])
async def get_comments_from_specified_task(task_id: int, session: AsyncSession = Depends(get_async_session)):
    query = (
        select(Comment)
        .filter_by(task_id=task_id)
        .options(joinedload(Comment.owner))
    )
    result = await session.execute(query)
    comments = result.scalars().all()
    return comments


@router.post("/upload", summary="Upload your Task file")
async def upload(
        task_id: int,
        session: AsyncSession = Depends(get_async_session),
        file: UploadFile = File(...),
        user: User = Depends(current_active_user)):
    with open(f"static/taskfiles/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    mimetype = file.content_type
    name = file.filename

    taskfile = TaskFile(name=name, minetype=mimetype, task_id=task_id, owner=user)
    session.add(taskfile)
    await session.commit()
    return f"{name} has been Successfully Uploaded"
