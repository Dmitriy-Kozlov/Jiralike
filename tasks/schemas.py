from datetime import datetime
from .models import TaskStatus
from pydantic import BaseModel


class CommentAdd(BaseModel):
    text: str
    task_id: int


class CommentRead(CommentAdd):
    id: int
    created_at: datetime


class TaskAdd(BaseModel):
    headline: str
    description: str


class TaskRead(TaskAdd):
    id: int
    status: TaskStatus
    created_at: datetime


class TaskFileAdd(BaseModel):
    name: str
    minetype: str
    task_id: int


class TaskFileRead(TaskFileAdd):
    id: int


from auth.schemas import UserRead


class TaskFileRel(TaskFileRead):
    task: "TaskRead"
    owner: "UserRead"


class CommentRel(CommentRead):
    # task: "TaskRead"
    owner: "UserRead"


class TaskRel(TaskRead):
    comments: list["CommentRel"]
    file: TaskFileRead | None
    owner: "UserRead"



#
# class Comment(BaseModel):
#     id: int
#     text: str
#     task_id: int
#
#     class Config:
#         from_attributes = True
#
#
# class BaseTask(BaseModel):
#     id: int
#     headline: str
#     description: str
#     date: datetime
#
#
# class Task(BaseTask):
#     comments: List[Comment] = []
#
#     class Config:
#         from_attributes = True
#
#
# class CreateTask(BaseTask):
#     pass
