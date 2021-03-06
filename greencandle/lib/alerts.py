#pylint: disable=no-member
"""
Functions for sending alerts
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import notify_run
from str2bool import str2bool
from . import config


def send_gmail_alert(action, pair, price):
    """
    Send email alert using gmail
    """
    if not str2bool(config.email.email_active):
        return
    email_to = config.email.email_to
    email_from = config.email.email_from
    email_password = config.email.email_password

    fromaddr = email_from
    toaddr = email_to
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    message = "{0} alert generated for {1} at {2}".format(action, pair, price)
    msg['Subject'] = message

    body = message
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_from, email_password)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def send_push_notif(*args):
    """
    Send push notification via notify.run
    """
    if not str2bool(config.push.push_active):
        return
    host = config.push.push_host
    channel = config.push.push_channel
    title = config.push.push_title
    try:
        base_host = "-{0}".format(os.environ['HOST'])
    except KeyError:
        base_host = ""
    text = title + base_host + ' ' + ' '.join(str(item) for item in args)
    notify = notify_run.Notify(channel)

    notify.endpoint = 'https://{0}/{1}'.format(host, channel)
    notify.send(text)
