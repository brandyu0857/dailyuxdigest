import logging
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_MAX_RETRIES = 3
SMTP_RETRY_DELAY = 5  # seconds


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

    last_error = None
    for attempt in range(1, SMTP_MAX_RETRIES + 1):
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
                server.login(sender, app_password)
                server.sendmail(sender, all_recipients, msg.as_string())
            logger.info("Email sent to %d subscribers (BCC).", len(subscribers))
            return
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check GMAIL_APP_PASSWORD.")
            raise
        except (smtplib.SMTPException, OSError) as e:
            last_error = e
            logger.warning(
                "SMTP attempt %d/%d failed: %s", attempt, SMTP_MAX_RETRIES, e
            )
            if attempt < SMTP_MAX_RETRIES:
                time.sleep(SMTP_RETRY_DELAY)

    logger.error("All %d SMTP attempts failed. Last error: %s", SMTP_MAX_RETRIES, last_error)
    raise RuntimeError(f"Failed to send email after {SMTP_MAX_RETRIES} attempts: {last_error}")
