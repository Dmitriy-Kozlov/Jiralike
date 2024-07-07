from datetime import datetime
from typing import List

from pydantic import BaseModel


class CommentAdd(BaseModel):
    text: str
    task_id: int


class Comment(CommentAdd):
    id: int
    created_at: datetime


class TaskAdd(BaseModel):
    headline: str
    description: str


class Task(TaskAdd):
    id: int
    created_at: datetime


class TaskFileAdd(BaseModel):
    name: str
    minetype: str
    task_id: int


class TaskFile(TaskFileAdd):
    id: int


class TaskFileRel(TaskFile):
    task: "Task"


class CommentRel(Comment):
    task: "Task"


class TaskRel(Task):
    comments: list["Comment"]
    file: TaskFile | None



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
