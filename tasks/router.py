import shutil
from typing import List, Generator

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlalchemy import select, insert, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
# from starlette.requests import Request

from auth.user_manager import current_active_user
from database import get_async_session
from .models import Task, Comment, TaskFile, EmailNotification, TaskStatus
from .schemas import TaskRel, TaskAdd, CommentAdd, CommentRead, CommentRel
from auth.models import User
from .send_email import send_email_notification

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/", response_model=List[TaskRel])
async def get_tasks(
        request: Request,
        task_filter: str = None,
        task_status: TaskStatus = None,
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
    if task_status:
        query = query.filter_by(status=task_status)
    result = await session.execute(query)
    tasks = result.scalars().all()
    token = request.cookies.get('bonds')
    from auth.user_manager import is_admin_token, get_jwt_strategy
    print(f"{token=}")
    print(is_admin_token(request, token, get_jwt_strategy().secret, get_jwt_strategy().token_audience, get_jwt_strategy().algorithm))
    return tasks


@router.get("/my_tasks", response_model=List[TaskRel], )
async def get_tasks(
        task_filter: str = None,
        task_status: TaskStatus = None,
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
    if task_status:
        query = query.filter_by(status=task_status)
    result = await session.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskRel)
async def get_one_task(task_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
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


@router.delete("/{task_id}")
async def get_one_task(task_id: int,
                       session: AsyncSession = Depends(get_async_session),
                       user: User = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete task")
    try:
        query = delete(Task).where(Task.id == task_id)
        await session.execute(query)
        await session.commit()
        return {"Message": "Task deleted"}
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Item not found")


@router.post("/")
async def add_task(
        new_task: TaskAdd,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user),
        ):
    new_task_db = Task(**new_task.dict(), owner=user)
    session.add(new_task_db)
    await session.flush()
    new_notification = EmailNotification(email=user.email, task_id=new_task_db.id)
    session.add(new_notification)
    await session.commit()
    background_tasks.add_task(send_email_notification, new_task_db.id, [user.email], session)
    return {"status": "OK"}


@router.post("/{task_id}/comment")
async def add_comment(
        new_comment: CommentAdd,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)):
    try:
        query = (
            select(Task)
            .filter_by(id=new_comment.task_id)
            .options(selectinload(Task.emails))
        )
        result = await session.execute(query)
        task = result.scalars().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == TaskStatus.closed:
        raise HTTPException(status_code=403, detail="Task is closed")

    new_comment_db = Comment(**new_comment.dict(), owner=user)
    email_list = [row.email for row in task.emails]
    if user.email not in email_list:
        new_notification = EmailNotification(email=user.email, task_id=new_comment_db.task_id)
        email_list.append(user.email)
        session.add(new_notification)
    session.add(new_comment_db)
    background_tasks.add_task(send_email_notification, new_comment_db.task_id, email_list, session)
    await session.commit()
    return {"status": "OK"}


@router.post("/{task_id}/close")
async def close_task(
        task_id: int,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)):
    try:
        query = (
            select(Task)
            .filter_by(id=task_id)
            .options(selectinload(Task.emails))
        )
        result = await session.execute(query)
        task = result.scalars().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot close this task")

    email_list = [row.email for row in task.emails]
    task.status = TaskStatus.closed
    session.add(task)
    background_tasks.add_task(send_email_notification, task_id, email_list, session)
    await session.commit()
    return {"status": "OK"}


@router.get("/{task_id}/comments", response_model=List[CommentRel])
async def get_comments_from_specified_task(task_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
        query = (
            select(Task)
            .filter_by(id=task_id)
            .options(selectinload(Task.comments))
        )
        result = await session.execute(query)
        task = result.scalars().one()
        return task.comments
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/upload", summary="Upload your Task file")
async def upload(
        task_id: int,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
        file: UploadFile = File(...),
        user: User = Depends(current_active_user)):
    try:
        query = (
            select(Task)
            .filter_by(id=task_id)
            .options(selectinload(Task.emails))
        )
        result = await session.execute(query)
        task = result.scalars().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")
    with open(f"static/taskfiles/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    mimetype = file.content_type
    name = file.filename

    taskfile = TaskFile(name=name, minetype=mimetype, task_id=task_id, owner=user)
    email_list = [row.email for row in task.emails]
    if user.email not in email_list:
        email_list.append(user.email)
    session.add(taskfile)
    await session.commit()
    background_tasks.add_task(send_email_notification, task_id, email_list, session)
    return f"{name} has been Successfully Uploaded"


@router.post("/download", summary="Download file for Task")
async def download(
        task_id: int,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)):
    try:
        query = (
            select(Task)
            .filter_by(id=task_id)
            .options(joinedload(Task.file))
            .options(selectinload(Task.emails))
        )
        result = await session.execute(query)
        task = result.scalars().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")
    path = f"static/taskfiles/{task.file.name}"
    email_list = [row.email for row in task.emails]
    if user.email not in email_list:
        email_list.append(user.email)
    background_tasks.add_task(send_email_notification, task_id, email_list, session)
    return FileResponse(path, media_type='application/octet-stream', filename=task.file.name)
