import datetime
import enum
from typing import Annotated, Optional

from sqlalchemy import String, ForeignKey, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base

created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]


class TaskStatus(enum.Enum):
    open = "open"
    closed = "closed"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    headline: Mapped[str]
    description: Mapped[str]
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.open)
    created_at: Mapped[created_at]
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    comments: Mapped[Optional[list["Comment"]]] = relationship(
        back_populates="task",
    )
    file: Mapped[Optional["TaskFile"]] = relationship(
        back_populates="task",
    )
    owner: Mapped["User"] = relationship(
        back_populates="tasks"
    )
    emails: Mapped[Optional[list["EmailNotification"]]] = relationship(
        back_populates="task",
    )

    def __repr__(self):
        return f"Task#{self.id}"


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str]
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[created_at]
    task: Mapped["Task"] = relationship(
        back_populates="comments",
    )
    owner: Mapped["User"] = relationship(
        back_populates="comments", lazy='selectin'
    )

    def __repr__(self):
        return self.text

class TaskFile(Base):
    __tablename__= "taskfiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    minetype: Mapped[str] = mapped_column(String(100))
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    task: Mapped["Task"] = relationship(
        back_populates="file",
    )
    owner: Mapped["User"] = relationship(
        back_populates="files"
    )

    def __repr__(self):
        return self.name


class EmailNotification(Base):
    __tablename__ = "emailnotifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    task: Mapped["Task"] = relationship(
        back_populates="emails",
    )

    def __repr__(self):
        return self.email