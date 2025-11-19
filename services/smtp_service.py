import smtplib
from email.message import EmailMessage

def send_email_smtp(to_email: str, subject: str, body: str, smtp_cfg: dict):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_cfg.get("from_email")
        msg["To"] = to_email
        msg.set_content(body)

        server = smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"])
        if smtp_cfg["use_tls"]:
            server.starttls()
        if smtp_cfg["username"]:
            server.login(smtp_cfg["username"], smtp_cfg["password"])

        server.send_message(msg)
        server.quit()
        return True, "Sent"

    except Exception as e:
        return False, str(e)
