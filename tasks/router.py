import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy import select, insert, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from auth.user_manager import current_active_user
from database import get_async_session
from .models import Task, Comment, TaskFile, EmailNotification
from .schemas import TaskRel, TaskAdd, CommentAdd, CommentRead, CommentRel
from auth.models import User
from .send_email import send_email_notification

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


@router.delete("/{task_id}")
async def get_one_task(task_id: int,
                       session: AsyncSession = Depends(get_async_session),
                       user: User = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete task")
    try:
        # session.query(Task).filter(Task.id == task_id).delete()
        # await session.commit()
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
    new_comment_db = Comment(**new_comment.dict(), owner=user)
    query = select(EmailNotification).filter_by(task_id=new_comment_db.task_id)
    result_emails = await session.execute(query)
    email_list = [row.email for row in result_emails.scalars().all()]
    if user.email not in email_list:
        new_notification = EmailNotification(email=user.email, task_id=new_comment_db.task_id)
        email_list.append(user.email)
        session.add(new_notification)
    session.add(new_comment_db)
    background_tasks.add_task(send_email_notification, new_comment_db.task_id, email_list, session)
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
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
        file: UploadFile = File(...),
        user: User = Depends(current_active_user)):
    with open(f"static/taskfiles/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    mimetype = file.content_type
    name = file.filename

    taskfile = TaskFile(name=name, minetype=mimetype, task_id=task_id, owner=user)
    query = select(EmailNotification).filter_by(task_id=task_id)
    result_emails = await session.execute(query)
    email_list = [row.email for row in result_emails.scalars().all()]
    session.add(taskfile)
    await session.commit()
    background_tasks.add_task(send_email_notification, task_id, email_list, session)
    return f"{name} has been Successfully Uploaded"
