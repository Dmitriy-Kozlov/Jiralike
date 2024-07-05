import datetime
from typing import Annotated, Optional

from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base

created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    headline: Mapped[str]
    description: Mapped[str]
    created_at: Mapped[created_at]
    comments: Mapped[Optional[list["Comment"]]] = relationship(
        back_populates="task",
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str]
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    created_at: Mapped[created_at]
    task: Mapped["Task"] = relationship(
        back_populates="comments",
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
