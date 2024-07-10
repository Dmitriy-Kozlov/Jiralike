import datetime
from typing import Annotated, Optional, List
from sqlalchemy.dialects.postgresql import ARRAY

from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base
# from auth.models import User

created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    headline: Mapped[str]
    description: Mapped[str]
    created_at: Mapped[created_at]
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    comments: Mapped[Optional[list["Comment"]]] = relationship(
        back_populates="task",
    )
    file: Mapped[Optional["TaskFile"]] = relationship(
        back_populates="task",
    )
    owner: Mapped["User"] = relationship(
        back_populates="tasks"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str]
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[created_at]
    task: Mapped["Task"] = relationship(
        back_populates="comments",
    )
    owner: Mapped["User"] = relationship(
        back_populates="comments", lazy='selectin'
    )


class TaskFile(Base):
    __tablename__= "taskfiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    minetype: Mapped[str] = mapped_column(String(100))
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    task: Mapped["Task"] = relationship(
        back_populates="file",
    )
    owner: Mapped["User"] = relationship(
        back_populates="files"
    )

#
#
# class Task(Base):
#     __tablename__ = "tasks"
#
#     id = Column("id", Integer, primary_key=True)
#     headline = Column("headline", String)
#     description = Column("description", String)
#     date = Column("date", TIMESTAMP)
#     comments = relationship("Comment", back_populates="task", lazy="selectin")
#
#
# class Comment(Base):
#     __tablename__ = "comments"
#
#     id = Column("id", Integer, primary_key=True)
#     text = Column("text", String)
#     task_id = Column(Integer, ForeignKey("tasks.id"))
#     task = relationship("Task", back_populates="comments", lazy="selectin")
