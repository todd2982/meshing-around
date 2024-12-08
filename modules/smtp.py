# SMTP module for the meshing-around bot
# 2024 Idea and code bits from https://github.com/tremmert81
# 2024 Kelly Keeton K7MHI

from modules.log import *
import pickle
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# SMTP settings
SMTP_SERVER = "smtp.gmail.com"  # Replace with your SMTP server
SMTP_PORT = 587  # 587 SMTP over TLS/STARTTLS, 25 legacy SMTP
FROM_EMAIL = "your_email@gmail.com"  # Sender email: be mindful of public access, don't use your personal email
SMTP_USERNAME = "your_email@gmail.com"  # Sender email username
SMTP_PASSWORD = "your_app_password"  # Sender email password
EMAIL_SUBJECT = "Meshtastic✉️"

trap_list_smtp = ("email", "setmail", "sms", "setsms")
smtpThrottle = {}

# Send email
def send_email(to_email, message):
    global smtpThrottle
    # if sent same to_email in last 2 minutes, throttle
    if to_email in smtpThrottle:
        if smtpThrottle[to_email] > time.time() - 120:
            logger.warning("System: Email throttled for " + to_email[:-6])
            return "⛔️Email throttled, try again later"
    smtpThrottle[to_email] = time.time()
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = EMAIL_SUBJECT
        msg.attach(MIMEText(message, 'plain'))

        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)

        # Send email
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()

        logger.info("System: Email sent to: " + to_email[:-6])
    except Exception as e:
        logger.warning("System: Failed to send email: " + str(e))
        return False
    return True

# initalize email db
email_db = {}
try:
    with open('data/email_db.pickle', 'rb') as f:
        email_db = pickle.load(f)
except:
    logger.warning("System: Email db not found, creating a new one")
    with open('data/email_db.pickle', 'wb') as f:
        pickle.dump(email_db, f)

def store_email(nodeID, email):
    global email_db
    # if not in db, add it
    logger.debug("System: Setting E-Mail for " + nodeID)
    if nodeID not in email_db:
        email_db[nodeID] = email
        return True
    # if in db, update it
    email_db[nodeID] = email

    # save to a pickle for persistence, this is a simple db, be mindful of risk
    with open('data/email_db.pickle', 'wb') as f:
        pickle.dump(email_db, f)
    return True

# initalize SMS db
sms_db = {}
try:
    with open('data/sms_db.pickle', 'rb') as f:
        sms_db = pickle.load(f)
except:
    logger.warning("System: SMS db not found, creating a new one")
    with open('data/sms_db.pickle', 'wb') as f:
        pickle.dump(sms_db, f)

def store_sms(nodeID, sms):
    global sms_db
    # if not in db, add it
    logger.debug("System: Setting SMS for " + nodeID)
    if nodeID not in sms_db:
        sms_db[nodeID] = sms
        return True
    # if in db, update it
    sms_db[nodeID] = sms

    # save to a pickle for persistence, this is a simple db, be mindful of risk
    with open('data/sms_db.pickle', 'wb') as f:
        pickle.dump(sms_db, f)
    return True

def handle_sms(nodeID, message):
    # send SMS to SMS in db. if none ask for one
    if message.lower.startswith("setsms"):
        message = message.split(" ", 1)
        if len(message) < 5:
            return "?📲setsms example@phone.co"
        if "@" not in message[1] and "." not in message[1]:
            return "📲Please provide a valid email address"
        if store_sms(nodeID, message[1]):
            return "📲SMS address set 📪"
        else:
            return "⛔️Failed to set address"
        
    if message.lower.startswith("sms"):
        message = message.split(" ", 1)
        if nodeID in sms_db:
            logger.info("System: Sending SMS for " + nodeID)
            send_email(sms_db[nodeID], message[1])
            return "📲SMS-sent 📤"
        else:
            return "📲No address set, use 📲setsms"
    
    return "Error: ⛔️ not understood. use:setsms example@phone.co"

def handle_email(nodeID, message):
    # send email to email in db. if none ask for one
    if message.lower.startswith("setmail"):
        message = message.split(" ", 1)
        if len(message) < 5:
            return "?📧setemail example@none.net"
        if "@" not in message[1] and "." not in message[1]:
            return "📧Please provide a valid email address"
        if store_email(nodeID, message[1]):
            return "📧Email address set 📪"

        return "Error: ⛔️ not understood. use:setmail bob@example.com"
        
    if message.lower.startswith("email"):
        message = message.split(" ", 1)

        # if user sent: email bob@none.net # Hello Bob
        if "@" in message[1] and "#" in message[1]:
            toEmail = message[0].strip()
            message = message[1].split("#", 1)
            logger.info("System: Sending email for " + nodeID)
            send_email(toEmail, message[1])
            return "📧Email-sent 📤"

        if nodeID in email_db:
            logger.info("System: Sending email for " + nodeID)
            send_email(email_db[nodeID], message[1])
            return "📧Email-sent 📤"

        return "Error: ⛔️ not understood. use:email bob@example.com # Hello Bob"
    
    