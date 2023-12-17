import smtplib
from password import GMAIL_ADDRESS, GMAIL_PASSWORD
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

ACCOUNT_CREATED = 0
ACCOUNT_ENABLED = 1
ACCOUNT_DISABLED = 2
ROLE_CHANGED = 3
CHANGE_EMAIL = 4

ACCOUNT_CREATED_MESSAGE = """
Dear {name}, 
<br><br>
Welcome to codebreaker!
<br><br>
An admin will activate your account in a few days. If your account is not activated, you may contact any admin or reply to this email. If you are new to competitive programming, you can consider trying our <a href = 'https://codebreaker.xyz/contest/starterproblems'>starter problems</a>.
<br><br>
Regards,
<br>
codebreaker.xyz
<br><br>
Note: this is an auto-generated email.
"""

ACCOUNT_CREATED_SUBJECT = "Welcome to Codebreaker!"

ACCOUNT_ENABLED_MESSAGE = """
Dear {name},
<br><br>
Your account at codebreaker.xyz has been enabled by administrator <a href = {link}>{changedby}</a>.
<br><br>
You may login to the website now.
<br><br>
Regards,
<br>
codebreaker.xyz
<br><br>
Note: this is an auto-generated email.
"""

ACCOUNT_ENABLED_SUBJECT = "Codebreaker Account Enabled"

ACCOUNT_DISABLED_MESSAGE = """
Dear {name},
<br><br>
Your account at codebreaker.xyz has been {newrole} by administrator <a href = {link}>{changedby}</a>.
<br><br>
You may contact the administrator if you think this is a mistake.
<br><br>
Regards,
<br>
codebreaker.xyz
<br><br>
Note: this is an auto-generated email.
"""

ACCOUNT_DISABLED_SUBJECT = "Codebreaker Account {newrole}"

ROLE_CHANGED_MESSAGE = """
Dear {name},
<br><br>
Your role at codebreaker.xyz has been updated to {newrole} by <a href = {link}>{changedby}</a>.
<br><br>
Regards,
<br>
codebreaker.xyz
<br><br>
Note: this is an auto-generated email.
"""

ROLE_CHANGED_SUBJECT = "Codebreaker Role Changed"


CHANGE_EMAIL_MESSSAGE = """
Dear {name},
<br><br>
You have requested an email change for the username {username} from {oldemail} to this email. By clicking on this <a href = {link}>link</a>, you will complete the email change process. 
<br><br>
Please note that this link is only valid for 15 minutes.
<br><br>
Regards,
<br>
codebreaker.xyz
<br><br>
Note: this is an auto-generated email.
"""

CHANGE_EMAIL_SUBJECT = "Codebreaker Email Change Request"

def sendEmail(info, type, changeinfo = None, newrole = None):

    msg = MIMEMultipart('alternative')

    receivers = [info['email']]

    msg['From'] = str(Header(f'Codebreaker <{GMAIL_ADDRESS}>'))
    msg['To'] = info['email']

    receivers += [GMAIL_ADDRESS]

    if changeinfo is not None:
        receivers += [changeinfo['email']]

    if type == ACCOUNT_CREATED:
        msg['Subject'] = ACCOUNT_CREATED_SUBJECT
        text = ACCOUNT_CREATED_MESSAGE.format(name = info['fullname'])

    if type == ACCOUNT_ENABLED:
        msg['Subject'] = ACCOUNT_ENABLED_SUBJECT
        text = ACCOUNT_ENABLED_MESSAGE.format(name = info['fullname'], 
        link = f'codebreaker.xyz/profile/{changeinfo["username"]}', changedby = changeinfo['username'])

    if type == ACCOUNT_DISABLED:
        msg['Subject'] = ACCOUNT_DISABLED_SUBJECT.format(newrole = newrole.title())
        text = ACCOUNT_DISABLED_MESSAGE.format(name = info['fullname'], newrole = newrole,
        link = f'codebreaker.xyz/profile/{changeinfo["username"]}', changedby = changeinfo['username'])

    if type == ROLE_CHANGED:
        msg['Subject'] = ROLE_CHANGED_SUBJECT
        text = ROLE_CHANGED_MESSAGE.format(name = info['fullname'], newrole = newrole,
        link = f'codebreaker.xyz/profile/{changeinfo["username"]}', changedby = changeinfo['username'])

    if type == CHANGE_EMAIL:
        msg['Subject'] = CHANGE_EMAIL_SUBJECT
        text = CHANGE_EMAIL_MESSSAGE.format(name = info['name'], username = info['username'], oldemail = info['oldemail'],
            link = info['link'])

    msg.attach(MIMEText(text, 'html'))

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
    s.sendmail(GMAIL_ADDRESS, receivers, msg.as_string())
    s.quit()

