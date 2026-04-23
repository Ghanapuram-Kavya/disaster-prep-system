from flask_mail import Mail, Message
from flask import Flask

mail = Mail()

def init_mail(app):
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'ghanapuramkavya7@gmail.com'  # 🔴 Your Gmail
    app.config['MAIL_PASSWORD'] = 'obdq ijid bmav krmu'   # 🔴 App Password
    app.config['MAIL_DEFAULT_SENDER'] = 'ghanapuramkavya7@gmail.com'
    mail.init_app(app)

def send_alert_email(to_emails, alert_title, alert_message, disaster_type):
    try:
        subject = f"🚨 DISASTER ALERT: {alert_title}"
        body = f"""
Dear Student,

⚠️ DISASTER ALERT NOTIFICATION ⚠️

Type: {disaster_type}
Alert: {alert_title}

Message:
{alert_message}

Please follow all safety instructions carefully.
Stay safe and follow emergency guidelines.

━━━━━━━━━━━━━━━━━━━━━━━━
Disaster Preparedness & Response System
This is an automated alert. Please do not reply.
        """
        msg = Message(subject=subject, recipients=to_emails, body=body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_quiz_result_email(to_email, student_name, lesson_title, score, total, percentage):
    try:
        subject = f"📊 Quiz Result: {lesson_title}"
        body = f"""
Dear {student_name},

Your quiz result is ready!

━━━━━━━━━━━━━━━━━━━━━━━━
📚 Lesson: {lesson_title}
✅ Score: {score}/{total}
📈 Percentage: {percentage:.1f}%
🏆 Grade: {"Excellent!" if percentage >= 80 else "Good!" if percentage >= 60 else "Keep Practicing!"}
━━━━━━━━━━━━━━━━━━━━━━━━

{"🎉 Congratulations! Outstanding performance!" if percentage >= 80 else "👍 Good effort! Keep learning!" if percentage >= 60 else "📖 Please review the lesson and try again!"}

Keep up the great work!

Disaster Preparedness & Response System
        """
        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_welcome_email(to_email, full_name, role):
    try:
        subject = "Welcome to Disaster Prep System! 🌪️"
        body = f"""
Dear {full_name},

Welcome to the Disaster Preparedness & Response Education System!

Your account has been created successfully.

━━━━━━━━━━━━━━━━━━━━━━━━
Role: {role.capitalize()}
Email: {to_email}
━━━━━━━━━━━━━━━━━━━━━━━━

{"As a Teacher you can: Add lessons, Create quizzes, Send alerts and Monitor student performance." if role == "teacher" else "As a Student you can: View lessons, Watch videos, Take quizzes and Track your progress."}

Login at: http://localhost:3000

Stay Safe!
Disaster Preparedness & Response System
        """
        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False