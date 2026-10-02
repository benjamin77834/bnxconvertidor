from pathlib import Path
from email.message import EmailMessage
from datetime import datetime, timezone
import smtplib

class ControlEmail:
    def __init__(self, cfg):
        self.cfg = cfg
        self.dir = Path("generated/emails")
        self.dir.mkdir(parents=True, exist_ok=True)
    def send(self, subject, body):
        if not self.cfg.get("enabled"):
            return
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["To"] = self.cfg["recipient"]
        msg["From"] = self.cfg.get("sender", "framework@example.com")
        msg.set_content(body)
        if self.cfg.get("mode", "file") == "file":
            name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".eml"
            (self.dir/name).write_bytes(bytes(msg))
        elif self.cfg["mode"] == "smtp":
            with smtplib.SMTP(self.cfg["smtp_host"], self.cfg.get("smtp_port",25)) as s:
                s.send_message(msg)
        else:
            raise ValueError("notification mode must be file or smtp")
