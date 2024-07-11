import os
import smtplib
import ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from config import EMAIL, EMAIL_PASSWORD, DEBAG
from tasks.models import Task

SMTP_SERVER = "smtp.gmail.com"
PORT = 465

if DEBAG:
    async def send_email_notification(task_id: int, email_list: list[str], session: AsyncSession):
        query = (
            select(Task)
            .filter_by(id=task_id)
            .options(selectinload(Task.comments))
            .options(joinedload(Task.file))
            .options(joinedload(Task.owner))
        )
        result = await session.execute(query)
        task = result.scalars().one()
        subject = task.headline
        body = f"{task.description}\nfrom user {task.owner.username}\n"
        if task.comments:
            body += "Comments:\n"
            body += "\n".join(f"{c.text} from user {c.owner.username}" for c in task.comments)


        message = MIMEMultipart()
        message["From"] = EMAIL
        # message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))
        if task.file:
            filename = f"static/taskfiles/{task.file.name}"

            with open(filename, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            message.attach(part)
        # text = message.as_string()

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, PORT, context=context) as server:
            server.login(EMAIL, EMAIL_PASSWORD)
            for receiver_email in email_list:
                message["To"] = receiver_email
                text = message.as_string()
                server.sendmail(EMAIL, receiver_email, text)
else:
    async def send_email_notification(task_id: int, email_list: list[str], session: AsyncSession):
        pass
