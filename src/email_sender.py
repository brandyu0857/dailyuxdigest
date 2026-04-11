import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email(html_content: str, subject: str, subscribers: list[str]) -> None:
    """Send the digest email to all subscribers via Gmail SMTP with BCC."""
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Daily UX Digest <{sender}>"
    msg["To"] = sender  # Send to self; subscribers are BCC'd

    msg.attach(MIMEText(html_content, "html"))

    # Build the full recipient list (sender + all BCC subscribers)
    all_recipients = [sender] + subscribers

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, all_recipients, msg.as_string())

    logger.info("Email sent to %d subscribers (BCC).", len(subscribers))
