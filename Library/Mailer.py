import smtplib
from email.mime.text import MIMEText


class Mailer:

    def __init__(self, from_email, from_password):
        self.from_email = from_email
        self.from_password = from_password
        self.smtpserver = smtplib.SMTP('smtp.gmail.com', 587)  # Server to use.
        self.send_mail_cooldown_seconds = None
        self.last_mail_sent_date = None

    def send_email(self, to_email, subject, msg):
        self.smtpserver.ehlo()  # Says 'hello' to the server
        self.smtpserver.starttls()  # Start TLS encryption
        self.smtpserver.ehlo()
        self.smtpserver.login(self.from_email, self.from_password)  # Log in to server

        msg = MIMEText(str(msg))
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to_email
        # Sends the message
        self.smtpserver.sendmail(self.from_email, [to_email], msg.as_string())
        # Closes the smtp server.
        self.smtpserver.quit()
