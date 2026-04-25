import os
import smtplib
from email.mime.text import MIMEText
from django.core.mail.backends.base import BaseEmailBackend

class FallbackEmailBackend(BaseEmailBackend):
    """
    Custom backend: try Vectra first, then Gmail if Vectra fails.
    """

    def send_messages(self, email_messages):
        providers = [
            {
                "name": "vectra",
                "host": "mail.vectra.ng",
                "port": 587,
                "user": os.getenv("VECTRA_USER"),
                "password": os.getenv("VECTRA_PASS"),
                "from_name": "Vectra Laundry"
            },
            {
                "name": "gmail",
                "host": "smtp.gmail.com",
                "port": 587,
                "user": os.getenv("GMAIL_USER"),
                "password": os.getenv("GMAIL_PASS"),
                "from_name": "Dignity Concept"
            }
        ]

        sent_count = 0
        for message in email_messages:
            body = message.body
            subject = message.subject
            to_email = message.to[0]

            for p in providers:
                try:
                    msg = MIMEText(body)
                    msg["Subject"] = subject
                    msg["From"] = f"{p['from_name']} <{p['user']}>"
                    msg["To"] = to_email

                    with smtplib.SMTP(p["host"], p["port"]) as server:
                        server.ehlo()
                        server.starttls()
                        server.login(p["user"], p["password"])
                        server.sendmail(p["user"], [to_email], msg.as_string())
                    print(f"✅ Email sent via {p['name']}")
                    sent_count += 1
                    break  # stop after success
                except Exception as e:
                    print(f"❌ Failed via {p['name']}: {e}")
        return sent_count
