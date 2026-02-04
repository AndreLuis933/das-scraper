import datetime
import os
import traceback
from pathlib import Path

import requests

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
DESTINATION_EMAIL = os.environ["DESTINATION_EMAIL"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]

def send_email(subject, html_content):
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={"from": SENDER_EMAIL, "to": [DESTINATION_EMAIL], "subject": subject, "html": html_content},
    )
    return response.json()


def load_template(template_name):

    template_path = os.path.join(Path(__file__).parent.parent, "template", template_name)
    with open(template_path, encoding="utf-8") as f:
        return f.read()


def notify_error(job_name):

    template = load_template("email_error.html")
    timestamp = datetime.datetime.now(tz=datetime.UTC).astimezone().strftime("%d/%m/%Y às %H:%M:%S")
    error_msg = traceback.format_exc()

    html = template.replace("{{JOB_NAME}}", job_name)
    html = html.replace("{{TIMESTAMP}}", timestamp)
    html = html.replace("{{ERROR_MESSAGE}}", error_msg)

    send_email(f"🚨 {job_name} - Falhou", html)

def notify_success(job_name):

    template = load_template("email_success.html")
    timestamp = datetime.datetime.now(tz=datetime.UTC).astimezone().strftime("%d/%m/%Y às %H:%M:%S")

    html = template.replace("{{JOB_NAME}}", job_name)
    html = html.replace("{{TIMESTAMP}}", timestamp)

    send_email(f"✅ {job_name} - Sucesso", html)

