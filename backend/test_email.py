import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL        = 'kavyaghanapuram@gmail.com'   # 🔴 Your Gmail
APP_PASSWORD = 'amux kqop mrtb mndz'    # 🔴 App Password
SEND_TO      = 'kavyaghanapuram@gmail.com'   # Send to yourself

msg = MIMEMultipart('alternative')
msg['Subject'] = 'Test Email - Disaster Prep System'
msg['From']    = GMAIL
msg['To']      = SEND_TO

plain = MIMEText('Test email working! Disaster Prep System', 'plain', 'utf-8')
html  = MIMEText('''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial;padding:20px">
  <div style="background:#e94560;padding:20px;border-radius:8px;
    text-align:center">
    <h2 style="color:white;margin:0">Disaster Prep System</h2>
    <p style="color:white;margin:8px 0 0">Email is working perfectly!</p>
  </div>
  <div style="padding:20px;background:#f5f5f5;margin-top:16px;
    border-radius:8px">
    <h3>Emergency Numbers</h3>
    <p>General: 112 | Fire: 101 | Ambulance: 102 | Police: 100</p>
  </div>
</body>
</html>''', 'html', 'utf-8')

msg.attach(plain)
msg.attach(html)

try:
    print(f"Connecting to Gmail...")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    print(f"Logging in as: {GMAIL}")
    server.login(GMAIL, APP_PASSWORD)
    print("Login successful!")
    server.sendmail(GMAIL, SEND_TO, msg.as_bytes())
    server.quit()
    print("="*50)
    print("SUCCESS! Email sent!")
    print(f"Check inbox: {SEND_TO}")
    print("="*50)
except smtplib.SMTPAuthenticationError:
    print("="*50)
    print("AUTHENTICATION FAILED!")
    print("Check your Gmail and App Password!")
    print("="*50)
except Exception as e:
    print(f"Error: {e}")