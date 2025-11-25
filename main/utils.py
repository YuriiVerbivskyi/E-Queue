import requests
import os

def send_notification_email(subject, message, recipient_email):
    mailgun_key = os.environ.get('MAILGUN_API_KEY')
    mailgun_domain = os.environ.get('MAILGUN_DOMAIN')
    default_from = os.environ.get('DEFAULT_FROM_EMAIL')
    print('SendMail params:', mailgun_key, mailgun_domain, default_from, recipient_email)
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
            auth=("api", mailgun_key),
            data={
                "from": default_from,
                "to": recipient_email,
                "subject": subject,
                "text": message
            }
        )
        print('Mailgun response:', response.status_code, response.text)
        return response.status_code == 200
    except Exception as e:
        print(f"Email error: {e}")
        return False
