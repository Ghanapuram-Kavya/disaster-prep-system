from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (JWTManager, create_access_token,
    jwt_required, get_jwt_identity)
from flask_mail import Mail, Message
from config import get_db
from certificate_service import generate_certificate
from ai_service import get_ai_response
from datetime import datetime, timedelta
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import io
import threading


# ── App setup ──────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ── JWT Config ─────────────────────────────────────────
app.config['JWT_SECRET_KEY']           = 'AIzaSyAAc-dPolnZCr7XMHjQIRhwoPsevgPGE5s'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
jwt = JWTManager(app)

# ── Mail Config ────────────────────────────────────────
app.config['MAIL_SERVER']         = 'smtp.gmail.com'
app.config['MAIL_PORT']           = 587
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USE_SSL']        = False
app.config['MAIL_USERNAME']       = 'kavyaghanapuram@gmail.com'
app.config['MAIL_PASSWORD']       = 'amux kqop mrtb mndz'
app.config['MAIL_DEFAULT_SENDER'] = 'kavyaghanapuram@gmail.com'
mail = Mail(app)

# ─── EMAIL HELPER ──────────────────────────────────────────

def send_email(to, subject, body):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        GMAIL        = 'kavyaghanapuram@gmail.com'
        APP_PASSWORD = 'amux kqop mrtb mndz'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f"Disaster Prep System <{GMAIL}>"
        msg['To']      = to

        clean_body = body.encode('ascii', 'ignore').decode('ascii')

        plain_text = f"""
DISASTER ALERT NOTIFICATION
============================

{clean_body}

============================
Emergency Numbers:
General Emergency : 112
Fire Department   : 101
Ambulance         : 102
Police            : 100
Disaster Helpline : 1070

Stay Safe!
Disaster Preparedness and Response System
        """

        html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;
  padding:20px;margin:0">
<div style="max-width:600px;margin:0 auto;background:white;
  border-radius:12px;overflow:hidden;
  box-shadow:0 4px 20px rgba(0,0,0,0.1)">
  <div style="background:linear-gradient(135deg,#1a1a2e,#e94560);
    padding:30px;text-align:center">
    <h1 style="color:white;margin:0;font-size:24px">
      Disaster Prep System
    </h1>
    <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px">
      Preparedness - Response - Education
    </p>
  </div>
  <div style="background:#e94560;padding:16px;text-align:center">
    <h2 style="color:white;margin:0;font-size:18px">
      URGENT ALERT: {subject}
    </h2>
  </div>
  <div style="padding:30px">
    <p style="color:#333;font-size:15px;line-height:1.8">
      {body.replace(chr(10), '<br>')}
    </p>
  </div>
  <div style="background:#fff3cd;padding:20px;margin:0 20px 20px;
    border-radius:8px;border-left:4px solid #f39c12">
    <h3 style="color:#856404;margin:0 0 16px;font-size:15px">
      Emergency Numbers - Save These!
    </h3>
    <table style="width:100%;border-collapse:collapse">
       <tr>
        <td style="padding:8px;background:white;border-radius:6px;
          text-align:center">
          <strong style="font-size:20px;color:#e94560;display:block">112</strong>
          <span style="font-size:11px;color:#777">General Emergency</span>
         </td>
        <td style="width:8px"></td>
        <td style="padding:8px;background:white;border-radius:6px;
          text-align:center">
          <strong style="font-size:20px;color:#e94560;display:block">101</strong>
          <span style="font-size:11px;color:#777">Fire Department</span>
         </td>
        <td style="width:8px"></td>
        <td style="padding:8px;background:white;border-radius:6px;
          text-align:center">
          <strong style="font-size:20px;color:#e94560;display:block">102</strong>
          <span style="font-size:11px;color:#777">Ambulance</span>
         </td>
        <td style="width:8px"></td>
        <td style="padding:8px;background:white;border-radius:6px;
          text-align:center">
          <strong style="font-size:20px;color:#e94560;display:block">100</strong>
          <span style="font-size:11px;color:#777">Police</span>
         </td>
       </tr>
     </table>
  </div>
  <div style="background:#1a1a2e;padding:20px;text-align:center">
    <p style="color:rgba(255,255,255,0.6);margin:0;font-size:12px">
      Be Prepared - Stay Safe - Save Lives
    </p>
    <p style="color:rgba(255,255,255,0.4);margin:6px 0 0;font-size:11px">
      Automated alert from Disaster Preparedness System
    </p>
  </div>
</div>
</body>
</html>"""

        text_part = MIMEText(plain_text, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(GMAIL, APP_PASSWORD)
        server.sendmail(GMAIL, to, msg.as_bytes())
        server.quit()
        print(f"Email sent to: {to}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(f"Authentication failed! Check Gmail and App Password")
        return False
    except Exception as e:
        print(f"Email error for {to}: {e}")
        return False


def send_bulk_email(to_list, subject, body):
    for email in to_list:
        send_email(email, subject, body)


# ─── SMS HELPER ──────────────────────────────────────────

def send_sms_safe(to_number, message):
    try:
        from sms_service import send_sms
        if to_number and to_number.strip():
            phone = to_number.strip()
            if not phone.startswith('+'):
                phone = '+91' + phone.lstrip('0')
            result = send_sms(phone, message)
            return result
    except ImportError:
        print("SMS service not configured - skipping SMS")
    except Exception as e:
        print(f"SMS error: {e}")
    return {'success': False}


# ─── ACTIVITY HELPER ──────────────────────────────────────────

def log_activity(student_id, activity_type, title,
                 description='', score=None, percentage=None):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO activities
            (student_id, activity_type, title,
            description, score, percentage)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (student_id, activity_type, title,
              description, score, percentage))
        db.commit()
        cursor.close()
        db.close()
        print(f"Activity logged: {activity_type} - {title}")
    except Exception as e:
        print(f"Activity log error: {e}")


# ─── BADGE HELPER ──────────────────────────────────────────

def check_and_award_badges(student_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(*) as quiz_count,
            SUM(CASE WHEN percentage = 100 THEN 1 ELSE 0 END) as perfect_count,
            SUM(CASE WHEN percentage >= 80 THEN 1 ELSE 0 END) as high_count
            FROM results WHERE student_id = %s
        """, (student_id,))
        quiz_stats = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) as assessment_count
            FROM assessment_results WHERE student_id = %s
        """, (student_id,))
        assessment_stats = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(DISTINCT l.id) as lesson_count
            FROM results r
            JOIN lessons l ON r.lesson_id = l.id
            WHERE r.student_id = %s
        """, (student_id,))
        lesson_stats = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) as streak
            FROM activities
            WHERE student_id = %s
            AND activity_type = 'login'
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (student_id,))
        streak_stats = cursor.fetchone()

        cursor.execute("""
            SELECT l.topic, COUNT(*) as count
            FROM results r
            JOIN lessons l ON r.lesson_id = l.id
            WHERE r.student_id = %s
            GROUP BY l.topic
        """, (student_id,))
        topic_stats = {row['topic']: row['count']
                      for row in cursor.fetchall()}

        cursor.execute("SELECT * FROM badges")
        all_badges = cursor.fetchall()

        cursor.execute("""
            SELECT badge_id FROM student_badges
            WHERE student_id = %s
        """, (student_id,))
        earned_ids = {row['badge_id'] for row in cursor.fetchall()}

        new_badges = []
        cursor2 = db.cursor()

        for badge in all_badges:
            if badge['id'] in earned_ids:
                continue
            should_award = False
            if badge['name'] == 'First Lesson' and \
               lesson_stats['lesson_count'] >= 1:
                should_award = True
            elif badge['name'] == 'Lesson Master' and \
               lesson_stats['lesson_count'] >= 5:
                should_award = True
            elif badge['name'] == 'Quiz Starter' and \
               quiz_stats['quiz_count'] >= 1:
                should_award = True
            elif badge['name'] == 'Quiz Champion' and \
               quiz_stats['quiz_count'] >= 10:
                should_award = True
            elif badge['name'] == 'Perfect Score' and \
               (quiz_stats['perfect_count'] or 0) >= 1:
                should_award = True
            elif badge['name'] == 'High Achiever' and \
               (quiz_stats['high_count'] or 0) >= 5:
                should_award = True
            elif badge['name'] == 'Assessment Ace' and \
               assessment_stats['assessment_count'] >= 1:
                should_award = True
            elif badge['name'] == 'Safety Expert' and \
               assessment_stats['assessment_count'] >= 4:
                should_award = True
            elif badge['name'] == 'Daily Learner' and \
               streak_stats['streak'] >= 3:
                should_award = True
            elif badge['name'] == 'Dedicated' and \
               streak_stats['streak'] >= 7:
                should_award = True
            elif badge['name'] == 'Earthquake Pro' and \
               topic_stats.get('Earthquake', 0) >= 1:
                should_award = True
            elif badge['name'] == 'Flood Expert' and \
               topic_stats.get('Flood', 0) >= 1:
                should_award = True
            elif badge['name'] == 'Fire Safety Pro' and \
               topic_stats.get('Fire', 0) >= 1:
                should_award = True
            elif badge['name'] == 'Cyclone Expert' and \
               topic_stats.get('Cyclone', 0) >= 1:
                should_award = True

            if should_award:
                try:
                    cursor2.execute("""
                        INSERT INTO student_badges
                        (student_id, badge_id)
                        VALUES (%s, %s)
                    """, (student_id, badge['id']))
                    new_badges.append(badge)
                    print(f"Badge awarded: {badge['name']}")
                except Exception as e:
                    print(f"Badge award error: {e}")

        db.commit()
        cursor.close()
        cursor2.close()
        db.close()
        return new_badges

    except Exception as e:
        print(f"Badge check error: {e}")
        return []


# ─── AUTH ROUTES ──────────────────────────────────────────

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data      = request.get_json()
        full_name = data.get('full_name', '').strip()
        email     = data.get('email', '').strip().lower()
        password  = data.get('password', '').strip()
        role      = data.get('role', '').strip()
        phone     = data.get('phone', '').strip()

        if not full_name:
            return jsonify({'message': 'Full name is required'}), 400
        if not email:
            return jsonify({'message': 'Email is required'}), 400
        if not password:
            return jsonify({'message': 'Password is required'}), 400
        if not role:
            return jsonify({'message': 'Role is required'}), 400
        if len(password) < 6:
            return jsonify({
                'message': 'Password must be at least 6 characters'
            }), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE email = %s", (email,)
        )
        if cursor.fetchone():
            cursor.close()
            db.close()
            return jsonify({
                'message': 'Email already exists! Please login instead.'
            }), 400

        hashed = bcrypt.generate_password_hash(
            password).decode('utf-8')
        cursor.execute(
            """INSERT INTO users
            (full_name, email, password, role, phone)
            VALUES (%s, %s, %s, %s, %s)""",
            (full_name, email, hashed, role, phone)
        )
        db.commit()
        new_id = cursor.lastrowid
        cursor.close()
        db.close()
        print(f"User created: {email} ID:{new_id}")

        try:
            send_email(
                email,
                "Welcome to Disaster Prep System!",
                f"Dear {full_name},\n\nWelcome!\nRole: {role}\n\nStay Safe!"
            )
        except Exception as e:
            print(f"Welcome email failed: {e}")

        return jsonify({'message': 'Account created successfully!'}), 201

    except Exception as e:
        print(f"Signup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data     = request.get_json()
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        if not email or not password:
            return jsonify({
                'message': 'Email and password required'
            }), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE email = %s", (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if not user:
            return jsonify({
                'message': 'No account found! Please sign up first.'
            }), 401

        if not bcrypt.check_password_hash(user['password'], password):
            return jsonify({
                'message': 'Wrong password! Please try again.'
            }), 401

        access_token = create_access_token(
            identity=json.dumps({
                'id'       : user['id'],
                'role'     : user['role'],
                'full_name': user['full_name']
            })
        )

        if user['role'] == 'student':
            log_activity(
                user['id'], 'login',
                'Logged into the system',
                f"Welcome back {user['full_name']}!"
            )

        print(f"Login successful: {email}")
        return jsonify({
            'token'    : access_token,
            'role'     : user['role'],
            'full_name': user['full_name'],
            'id'       : user['id']
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Error: {str(e)}'}), 500


# ─── ROLE SWITCH ROUTE ──────────────────────────────────────────

@app.route('/api/switch-role', methods=['POST'])
@jwt_required()
def switch_role():
    current_user = json.loads(get_jwt_identity())
    data        = request.get_json()
    target_role = data.get('target_role')
    password    = data.get('password', '')

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (current_user['id'],)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if not user:
            return jsonify({'message': 'User not found'}), 404

        if target_role == 'teacher':
            if not password:
                return jsonify({
                    'message': 'Password required to switch to teacher!'
                }), 400
            if not bcrypt.check_password_hash(
                user['password'], password
            ):
                return jsonify({'message': 'Wrong password!'}), 401

        new_token = create_access_token(
            identity=json.dumps({
                'id'       : user['id'],
                'role'     : target_role,
                'full_name': user['full_name']
            })
        )

        if target_role == 'student':
            log_activity(
                user['id'], 'login',
                'Switched to student view',
                'Role switched from teacher to student'
            )

        return jsonify({
            'message'  : f'Switched to {target_role}!',
            'token'    : new_token,
            'role'     : target_role,
            'full_name': user['full_name']
        }), 200

    except Exception as e:
        print(f"Role switch error: {e}")
        return jsonify({'message': str(e)}), 500


# ─── LESSON ROUTES ──────────────────────────────────────────

@app.route('/api/lessons', methods=['GET'])
@jwt_required()
def get_lessons():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT l.*, u.full_name as teacher_name
            FROM lessons l
            JOIN users u ON l.created_by = u.id
        """)
        lessons = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(lessons), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/lessons', methods=['POST'])
@jwt_required()
def add_lesson():
    data = request.get_json()
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO lessons
            (title, topic, content, video_url, created_by)
            VALUES (%s,%s,%s,%s,%s)""",
            (data['title'], data['topic'], data['content'],
             data['video_url'], current_user['id'])
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Lesson added!'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>', methods=['PUT'])
@jwt_required()
def update_lesson(lesson_id):
    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'teacher':
        return jsonify({'message': 'Teachers only!'}), 403
    data = request.get_json()
    try:
        print(f"Updating lesson {lesson_id}: {data}")
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE lessons
            SET title     = %s,
                topic     = %s,
                content   = %s,
                video_url = %s
            WHERE id = %s
        """, (
            data.get('title'),
            data.get('topic'),
            data.get('content'),
            data.get('video_url'),
            lesson_id
        ))
        db.commit()
        affected = cursor.rowcount
        cursor.close()
        db.close()
        print(f"Lesson {lesson_id} updated! Rows: {affected}")
        return jsonify({
            'message': 'Lesson updated successfully!'
        }), 200
    except Exception as e:
        print(f"Update lesson error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>', methods=['DELETE'])
@jwt_required()
def delete_lesson(lesson_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM lessons WHERE id = %s", (lesson_id,)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Lesson deleted!'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── QUIZ ROUTES ──────────────────────────────────────────

@app.route('/api/quizzes/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_quizzes(lesson_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM quizzes WHERE lesson_id = %s",
            (lesson_id,)
        )
        quizzes = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(quizzes), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/quizzes', methods=['POST'])
@jwt_required()
def add_quiz():
    data = request.get_json()
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO quizzes
            (lesson_id, question, option_a, option_b,
            option_c, option_d, correct_option)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (data['lesson_id'], data['question'],
             data['option_a'], data['option_b'],
             data['option_c'], data['option_d'],
             data['correct_option'])
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Quiz added!'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── RESULTS ROUTES ──────────────────────────────────────────

@app.route('/api/results', methods=['POST'])
@jwt_required()
def save_result():
    data = request.get_json()
    current_user = json.loads(get_jwt_identity())
    percentage = (data['score'] / data['total_questions']) * 100
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO results
            (student_id, lesson_id, score, total_questions, percentage)
            VALUES (%s,%s,%s,%s,%s)""",
            (current_user['id'], data['lesson_id'],
             data['score'], data['total_questions'], percentage)
        )
        db.commit()

        cursor2 = db.cursor(dictionary=True)
        cursor2.execute(
            "SELECT email, full_name FROM users WHERE id=%s",
            (current_user['id'],)
        )
        student = cursor2.fetchone()
        cursor2.execute(
            "SELECT title FROM lessons WHERE id=%s",
            (data['lesson_id'],)
        )
        lesson = cursor2.fetchone()
        cursor2.close()
        cursor.close()
        db.close()

        grade = ("A+" if percentage >= 90 else
                 "A"  if percentage >= 80 else
                 "B"  if percentage >= 70 else
                 "C"  if percentage >= 60 else "F")

        log_activity(
            current_user['id'], 'quiz',
            f"Completed quiz: {lesson['title']}",
            f"Scored {data['score']} out of "
            f"{data['total_questions']} — Grade: {grade}",
            data['score'], percentage
        )

        check_and_award_badges(current_user['id'])

        try:
            send_email(
                student['email'],
                f"Quiz Result: {lesson['title']}",
                f"Dear {student['full_name']},\n\n"
                f"Score: {data['score']}/{data['total_questions']}\n"
                f"Percentage: {percentage:.1f}%\nGrade: {grade}"
            )
        except Exception as e:
            print(f"Email error: {e}")

        return jsonify({
            'message'   : 'Result saved!',
            'percentage': percentage
        }), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/results/student', methods=['GET'])
@jwt_required()
def get_student_results():
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, l.title, l.topic
            FROM results r
            JOIN lessons l ON r.lesson_id = l.id
            WHERE r.student_id = %s
            ORDER BY r.completed_at DESC
        """, (current_user['id'],))
        results = cursor.fetchall()
        for r in results:
            if hasattr(r.get('completed_at'), 'isoformat'):
                r['completed_at'] = r['completed_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/results/all', methods=['GET'])
@jwt_required()
def get_all_results():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, u.full_name, l.title, l.topic
            FROM results r
            JOIN users u ON r.student_id = u.id
            JOIN lessons l ON r.lesson_id = l.id
            ORDER BY r.percentage DESC
        """)
        results = cursor.fetchall()
        for r in results:
            if hasattr(r.get('completed_at'), 'isoformat'):
                r['completed_at'] = r['completed_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── ALERTS ROUTES ──────────────────────────────────────────

@app.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, u.full_name as sent_by_name
            FROM alerts a
            JOIN users u ON a.created_by = u.id
            ORDER BY a.created_at DESC
        """)
        alerts = cursor.fetchall()
        for a in alerts:
            if hasattr(a.get('created_at'), 'isoformat'):
                a['created_at'] = a['created_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(alerts), 200
    except Exception as e:
        print(f"Get alerts error: {e}")
        return jsonify({'message': str(e)}), 500


@app.route('/api/alerts', methods=['POST'])
@jwt_required()
def add_alert():
    try:
        data          = request.get_json()
        current_user  = json.loads(get_jwt_identity())
        title         = data.get('title', '').strip()
        message       = data.get('message', '').strip()
        disaster_type = data.get('disaster_type', 'General')

        if not title:
            return jsonify({'message': 'Title is required'}), 400
        if not message:
            return jsonify({'message': 'Message is required'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO alerts
            (title, message, disaster_type, created_by)
            VALUES (%s, %s, %s, %s)""",
            (title, message, disaster_type, current_user['id'])
        )
        db.commit()

        cursor2 = db.cursor(dictionary=True)
        cursor2.execute(
            "SELECT email, full_name, phone FROM users "
            "WHERE role='student'"
        )
        students = cursor2.fetchall()
        cursor2.close()
        cursor.close()
        db.close()

        def send_notifications():
            emails_sent = 0
            for student in students:
                try:
                    if student.get('email'):
                        send_email(
                            student['email'],
                            f"URGENT ALERT: {title}",
                            f"""DISASTER ALERT NOTIFICATION

Type    : {disaster_type}
Alert   : {title}

Message : {message}

Stay safe and follow all safety instructions!

Emergency Numbers:
General   : 112
Fire      : 101
Ambulance : 102
Police    : 100
Disaster  : 1070

Disaster Preparedness System"""
                        )
                        emails_sent += 1
                        print(f"Email sent to: {student['email']}")

                    try:
                        db2 = get_db()
                        cur = db2.cursor(dictionary=True)
                        cur.execute("""
                            SELECT ec.email, ec.name, u.full_name
                            FROM emergency_contacts ec
                            JOIN users u ON ec.student_id = u.id
                            WHERE ec.student_id = (
                                SELECT id FROM users WHERE email = %s
                            )
                            AND ec.email != ''
                        """, (student['email'],))
                        em_contacts = cur.fetchall()
                        cur.close()
                        db2.close()
                        for ec in em_contacts:
                            send_email(
                                ec['email'],
                                f"ALERT for {ec['full_name']}: {title}",
                                f"Your family member {ec['full_name']} "
                                f"received a disaster alert.\n\n"
                                f"Type: {disaster_type}\n"
                                f"Alert: {title}\n"
                                f"Message: {message}\n\n"
                                f"Please ensure they are safe!\n"
                                f"Emergency: 112"
                            )
                    except Exception as ec_err:
                        print(f"EC alert error: {ec_err}")

                except Exception as e:
                    print(f"Email error: {e}")

            try:
                phones = []
                for s in students:
                    if s.get('phone') and s['phone'].strip():
                        phone = s['phone'].strip()
                        if not phone.startswith('+'):
                            phone = '+91' + phone.lstrip('0')
                        phones.append(phone)
                if phones:
                    sent = 0
                    for phone in phones:
                        result = send_sms_safe(
                            phone,
                            f"DISASTER ALERT!\n"
                            f"Type: {disaster_type}\n"
                            f"{title}\n{message}\n"
                            f"Emergency: 112"
                        )
                        if result.get('success'):
                            sent += 1
                    print(f"SMS sent to {sent}/{len(phones)} students")
            except Exception as e:
                print(f"SMS error: {e}")

            print(f"Notifications complete! Emails:{emails_sent}")

        thread = threading.Thread(target=send_notifications)
        thread.daemon = True
        thread.start()

        return jsonify({
            'message'           : 'Alert sent successfully!',
            'students_notified' : len(students),
            'emails_sent'       : 'sending in background...',
            'sms_sent'          : 'sending in background...'
        }), 201

    except Exception as e:
        print(f"Alert error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500


# ─── CERTIFICATE ROUTE ──────────────────────────────────────────

@app.route('/api/certificate/<int:result_id>', methods=['GET'])
@jwt_required()
def download_certificate(result_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, u.full_name, l.title as lesson_title
            FROM results r
            JOIN users u ON r.student_id = u.id
            JOIN lessons l ON r.lesson_id = l.id
            WHERE r.id = %s
        """, (result_id,))
        result = cursor.fetchone()
        cursor.close()
        db.close()

        if not result:
            return jsonify({'message': 'Result not found'}), 404
        if result['percentage'] < 60:
            return jsonify({'message': 'Minimum 60% required'}), 400

        log_activity(
            result['student_id'], 'certificate',
            f"Downloaded certificate: {result['lesson_title']}",
            f"Achieved {result['percentage']:.1f}% — Certificate earned!",
            result['score'], result['percentage']
        )

        buffer = generate_certificate(
            result['full_name'], result['lesson_title'],
            result['score'], result['total_questions'],
            result['percentage']
        )
        return send_file(
            buffer, as_attachment=True,
            download_name=f"certificate_{result['full_name']}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── LEADERBOARD ──────────────────────────────────────────

@app.route('/api/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                u.id, u.full_name,
                COUNT(DISTINCT r.id) as quizzes_taken,
                COUNT(DISTINCT ar.id) as assessments_taken,
                COUNT(DISTINCT r.id) +
                COUNT(DISTINCT ar.id) as total_activities,
                COALESCE(AVG(r.percentage), 0) as quiz_avg,
                COALESCE(AVG(ar.percentage), 0) as assessment_avg,
                ROUND((
                    COALESCE(AVG(r.percentage), 0) +
                    COALESCE(AVG(ar.percentage), 0)
                ) / CASE
                    WHEN AVG(r.percentage) IS NOT NULL
                    AND AVG(ar.percentage) IS NOT NULL THEN 2
                    WHEN AVG(r.percentage) IS NOT NULL THEN 1
                    WHEN AVG(ar.percentage) IS NOT NULL THEN 1
                    ELSE 1 END, 1) as overall_avg,
                COALESCE(SUM(r.score), 0) +
                COALESCE(SUM(ar.score), 0) as total_score
            FROM users u
            LEFT JOIN results r ON u.id = r.student_id
            LEFT JOIN assessment_results ar ON u.id = ar.student_id
            WHERE u.role = 'student'
            GROUP BY u.id, u.full_name
            ORDER BY overall_avg DESC, total_activities DESC
        """)
        leaderboard = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(leaderboard), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── ASSESSMENT ROUTES ──────────────────────────────────────────

@app.route('/api/assessments', methods=['GET'])
@jwt_required()
def get_assessments():
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if current_user['role'] == 'teacher':
            cursor.execute("""
                SELECT a.*,
                u.full_name as teacher_name,
                COUNT(DISTINCT aq.id) as total_questions,
                COALESCE(a.assigned_to, 'all') as assigned_to,
                (SELECT COUNT(*) FROM assessment_assignments aa
                 WHERE aa.assessment_id = a.id
                ) as assigned_count
                FROM assessments a
                JOIN users u ON a.created_by = u.id
                LEFT JOIN assessment_questions aq
                    ON a.id = aq.assessment_id
                GROUP BY a.id
                ORDER BY a.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT DISTINCT a.*,
                u.full_name as teacher_name,
                COUNT(DISTINCT aq.id) as total_questions,
                COALESCE(a.assigned_to, 'all') as assigned_to
                FROM assessments a
                JOIN users u ON a.created_by = u.id
                LEFT JOIN assessment_questions aq
                    ON a.id = aq.assessment_id
                WHERE
                    COALESCE(a.assigned_to, 'all') = 'all'
                    OR a.id IN (
                        SELECT assessment_id
                        FROM assessment_assignments
                        WHERE student_id = %s
                    )
                GROUP BY a.id
                ORDER BY a.deadline ASC
            """, (current_user['id'],))

        assessments = cursor.fetchall()
        for a in assessments:
            if hasattr(a.get('deadline'), 'isoformat'):
                a['deadline'] = a['deadline'].isoformat()
            if hasattr(a.get('created_at'), 'isoformat'):
                a['created_at'] = a['created_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(assessments), 200

    except Exception as e:
        print(f"Get assessments error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500


@app.route('/api/assessments', methods=['POST'])
@jwt_required()
def add_assessment():
    data = request.get_json()
    current_user = json.loads(get_jwt_identity())
    try:
        assigned_to = data.get('assigned_to', 'all')
        student_ids = data.get('student_ids', [])

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                """INSERT INTO assessments
                (title, topic, description, video_url,
                deadline, duration_minutes, created_by, assigned_to)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (data['title'], data['topic'],
                 data['description'], data['video_url'],
                 data['deadline'], data['duration_minutes'],
                 current_user['id'], assigned_to)
            )
        except Exception:
            cursor.execute(
                """INSERT INTO assessments
                (title, topic, description, video_url,
                deadline, duration_minutes, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (data['title'], data['topic'],
                 data['description'], data['video_url'],
                 data['deadline'], data['duration_minutes'],
                 current_user['id'])
            )

        db.commit()
        assessment_id = cursor.lastrowid

        for q in data.get('questions', []):
            cursor.execute(
                """INSERT INTO assessment_questions
                (assessment_id, question, option_a, option_b,
                option_c, option_d, correct_option)
                VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (assessment_id, q['question'],
                 q['option_a'], q['option_b'],
                 q['option_c'], q['option_d'],
                 q['correct_option'])
            )

        if assigned_to == 'specific' and student_ids:
            for sid in student_ids:
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO assessment_assignments
                        (assessment_id, student_id)
                        VALUES (%s, %s)
                    """, (assessment_id, sid))
                except Exception as e:
                    print(f"Assignment error: {e}")

        db.commit()
        cursor.close()
        db.close()
        return jsonify({
            'message': 'Assessment created!',
            'id'     : assessment_id
        }), 201

    except Exception as e:
        print(f"Add assessment error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500


@app.route('/api/assessments/<int:assessment_id>/assign',
           methods=['POST'])
@jwt_required()
def assign_assessment(assessment_id):
    current_user = json.loads(get_jwt_identity())
    data         = request.get_json()
    student_ids  = data.get('student_ids', [])
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            DELETE FROM assessment_assignments
            WHERE assessment_id = %s
        """, (assessment_id,))

        for sid in student_ids:
            cursor.execute("""
                INSERT IGNORE INTO assessment_assignments
                (assessment_id, student_id)
                VALUES (%s, %s)
            """, (assessment_id, sid))

        assigned_to = 'specific' if student_ids else 'all'
        cursor.execute("""
            UPDATE assessments SET assigned_to = %s
            WHERE id = %s
        """, (assigned_to, assessment_id))

        db.commit()

        cursor2 = db.cursor(dictionary=True)
        cursor2.execute("""
            SELECT a.*, u.full_name as teacher_name
            FROM assessments a
            JOIN users u ON a.created_by = u.id
            WHERE a.id = %s
        """, (assessment_id,))
        assessment = cursor2.fetchone()

        if student_ids:
            format_ids = ','.join(['%s'] * len(student_ids))
            cursor2.execute(f"""
                SELECT id, full_name, email, phone
                FROM users
                WHERE id IN ({format_ids}) AND role = 'student'
            """, tuple(student_ids))
            students = cursor2.fetchall()
        else:
            cursor2.execute("""
                SELECT id, full_name, email, phone
                FROM users WHERE role = 'student'
            """)
            students = cursor2.fetchall()

        cursor2.close()
        cursor.close()
        db.close()

        def send_assignment_emails():
            emails_sent = 0
            for student in students:
                try:
                    if student.get('email'):
                        deadline_str = ''
                        if assessment.get('deadline'):
                            if isinstance(assessment['deadline'], str):
                                deadline_str = assessment['deadline']
                            else:
                                deadline_str = assessment[
                                    'deadline'
                                ].strftime('%d %B %Y at %I:%M %p')

                        send_email(
                            student['email'],
                            f"New Assessment Assigned: "
                            f"{assessment['title']}",
                            f"""Dear {student['full_name']},

A new assessment has been assigned to you!

Title       : {assessment['title']}
Topic       : {assessment['topic']}
Description : {assessment['description']}
Duration    : {assessment['duration_minutes']} minutes
Deadline    : {deadline_str}
Assigned by : {assessment['teacher_name']}

Log in to complete it before the deadline!

Good luck!
Disaster Preparedness System"""
                        )
                        emails_sent += 1

                    if student.get('phone'):
                        send_sms_safe(
                            student['phone'],
                            f"New Assessment: {assessment['title']}\n"
                            f"Topic: {assessment['topic']}\n"
                            f"Login to complete it!"
                        )

                except Exception as e:
                    print(f"Assignment email error: {e}")

            print(f"Assignment emails: {emails_sent}/{len(students)}")

        thread = threading.Thread(target=send_assignment_emails)
        thread.daemon = True
        thread.start()

        return jsonify({
            'message'           : f'Assigned to {len(student_ids)} '
                                   f'students! Emails sent!',
            'students_notified' : len(student_ids)
        }), 200

    except Exception as e:
        print(f"Assign error: {e}")
        return jsonify({'message': str(e)}), 500


@app.route('/api/assessments/<int:assessment_id>/assignments',
           methods=['GET'])
@jwt_required()
def get_assessment_assignments(assessment_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT aa.student_id, u.full_name, u.email
            FROM assessment_assignments aa
            JOIN users u ON aa.student_id = u.id
            WHERE aa.assessment_id = %s
        """, (assessment_id,))
        assignments = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(assignments), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/assessments/<int:assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment_detail(assessment_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM assessments WHERE id=%s", (assessment_id,)
        )
        assessment = cursor.fetchone()
        if assessment:
            if hasattr(assessment.get('deadline'), 'isoformat'):
                assessment['deadline'] = \
                    assessment['deadline'].isoformat()
            if hasattr(assessment.get('created_at'), 'isoformat'):
                assessment['created_at'] = \
                    assessment['created_at'].isoformat()
        cursor.execute(
            "SELECT * FROM assessment_questions "
            "WHERE assessment_id=%s",
            (assessment_id,)
        )
        questions = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify({
            'assessment': assessment,
            'questions' : questions
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/assessments/<int:assessment_id>',
           methods=['DELETE'])
@jwt_required()
def delete_assessment(assessment_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM assessment_questions "
            "WHERE assessment_id=%s", (assessment_id,)
        )
        cursor.execute(
            "DELETE FROM assessment_results "
            "WHERE assessment_id=%s", (assessment_id,)
        )
        cursor.execute(
            "DELETE FROM assessment_assignments "
            "WHERE assessment_id=%s", (assessment_id,)
        )
        cursor.execute(
            "DELETE FROM assessments WHERE id=%s", (assessment_id,)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Assessment deleted!'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/assessments/submit', methods=['POST'])
@jwt_required()
def submit_assessment():
    data         = request.get_json()
    current_user = json.loads(get_jwt_identity())
    try:
        db     = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM assessment_questions "
            "WHERE assessment_id = %s",
            (data['assessment_id'],)
        )
        questions = cursor.fetchall()

        score      = 0
        answers    = data.get('answers', {})
        time_taken = data.get('time_taken', 0)

        import json as json_lib
        question_results = []
        for q in questions:
            student_answer = answers.get(str(q['id']), '')
            is_correct     = student_answer == q['correct_option']
            if is_correct:
                score += 1
            question_results.append({
                'question_id'   : q['id'],
                'question'      : q['question'],
                'option_a'      : q['option_a'],
                'option_b'      : q['option_b'],
                'option_c'      : q['option_c'],
                'option_d'      : q['option_d'],
                'correct_option': q['correct_option'],
                'student_answer': student_answer,
                'is_correct'    : is_correct
            })

        total        = len(questions)
        percentage   = (score / total * 100) if total > 0 else 0
        answers_json = json_lib.dumps(question_results)

        cursor2 = db.cursor()
        cursor2.execute("""
            INSERT INTO assessment_results
            (assessment_id, student_id, score,
             total_questions, percentage,
             status, answers_json, time_taken)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data['assessment_id'], current_user['id'],
            score, total, percentage,
            data.get('status', 'completed'),
            answers_json, time_taken
        ))
        db.commit()
        result_id = cursor2.lastrowid

        cursor.execute(
            "SELECT email, full_name FROM users WHERE id=%s",
            (current_user['id'],)
        )
        student = cursor.fetchone()

        cursor.execute(
            "SELECT title, topic FROM assessments WHERE id=%s",
            (data['assessment_id'],)
        )
        assessment_data = cursor.fetchone()
        cursor.close()
        cursor2.close()
        db.close()

        grade = ("A+" if percentage >= 90 else
                 "A"  if percentage >= 80 else
                 "B"  if percentage >= 70 else
                 "C"  if percentage >= 60 else "F")

        log_activity(
            current_user['id'], 'assessment',
            f"Completed: {assessment_data['title']}",
            f"Score {score}/{total} Grade:{grade}",
            score, percentage
        )
        check_and_award_badges(current_user['id'])

        if percentage < 60:
            suggestion = (
                f"You scored {percentage:.0f}% on "
                f"{assessment_data['topic']}. Focus on reviewing "
                f"the core concepts and retry the assessment!"
            )
        elif percentage < 80:
            suggestion = (
                f"Good effort! You scored {percentage:.0f}%. "
                f"Review the wrong answers to improve further!"
            )
        else:
            suggestion = (
                f"Excellent! {percentage:.0f}% is outstanding. "
                f"Keep up the great work!"
            )

        try:
            send_email(
                student['email'],
                f"Assessment Result: {assessment_data['title']}",
                f"Dear {student['full_name']},\n\n"
                f"Score: {score}/{total}\n"
                f"Percentage: {percentage:.1f}%\n"
                f"Grade: {grade}\n\n{suggestion}"
            )
        except Exception as e:
            print(f"Email error: {e}")

        return jsonify({
            'message'         : 'Submitted successfully!',
            'result_id'       : result_id,
            'score'           : score,
            'total'           : total,
            'percentage'      : percentage,
            'grade'           : grade,
            'suggestion'      : suggestion,
            'question_results': question_results,
            'time_taken'      : time_taken
        }), 201

    except Exception as e:
        print(f"Submit assessment error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/assessments/results/all', methods=['GET'])
@jwt_required()
def get_all_assessment_results():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT ar.*, u.full_name, a.title, a.topic, a.deadline
            FROM assessment_results ar
            JOIN users u ON ar.student_id = u.id
            JOIN assessments a ON ar.assessment_id = a.id
            ORDER BY ar.submitted_at DESC
        """)
        results = cursor.fetchall()
        for r in results:
            if hasattr(r.get('deadline'), 'isoformat'):
                r['deadline'] = r['deadline'].isoformat()
            if hasattr(r.get('submitted_at'), 'isoformat'):
                r['submitted_at'] = r['submitted_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/assessments/results/student', methods=['GET'])
@jwt_required()
def get_student_assessment_results():
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT ar.*, a.title, a.topic, a.deadline, a.video_url
            FROM assessment_results ar
            JOIN assessments a ON ar.assessment_id = a.id
            WHERE ar.student_id = %s
            ORDER BY ar.submitted_at DESC
        """, (current_user['id'],))
        results = cursor.fetchall()
        for r in results:
            if hasattr(r.get('deadline'), 'isoformat'):
                r['deadline'] = r['deadline'].isoformat()
            if hasattr(r.get('submitted_at'), 'isoformat'):
                r['submitted_at'] = r['submitted_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/assessments/<int:assessment_id>/history',methods=['GET'])
@jwt_required()
def get_assessment_history(assessment_id):
    current_user = json.loads(get_jwt_identity())
    try:
        import json as json_lib
        db     = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT ar.*, a.title, a.topic, a.description
            FROM assessment_results ar
            JOIN assessments a ON ar.assessment_id = a.id
            WHERE ar.student_id = %s
            AND ar.assessment_id = %s
            ORDER BY ar.submitted_at DESC
        """, (current_user['id'], assessment_id))

        results = cursor.fetchall()

        for r in results:
            if hasattr(r.get('submitted_at'), 'isoformat'):
                r['submitted_at'] = r['submitted_at'].isoformat()
            if r.get('answers_json'):
                try:
                    r['question_results'] = json_lib.loads(
                        r['answers_json']
                    )
                except:
                    r['question_results'] = []
            else:
                r['question_results'] = []
            r.pop('answers_json', None)

        cursor.close()
        db.close()

        return jsonify({
            'history'    : results,
            'total_attempts': len(results),
            'best_score' : max(
                [r['percentage'] for r in results], default=0
            ),
            'latest_score': results[0]['percentage'] if results else 0
        }), 200

    except Exception as e:
        print(f"History error: {e}")
        return jsonify({'message': str(e)}), 500


# ─── EVACUATION ROUTES ──────────────────────────────────────────

@app.route('/api/evacuation', methods=['GET'])
@jwt_required()
def get_evacuation_routes():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, u.full_name as created_by_name
            FROM evacuation_routes e
            JOIN users u ON e.created_by = u.id
            ORDER BY e.disaster_type
        """)
        routes = cursor.fetchall()
        for r in routes:
            if hasattr(r.get('created_at'), 'isoformat'):
                r['created_at'] = r['created_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(routes), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/evacuation', methods=['POST'])
@jwt_required()
def add_evacuation_route():
    data = request.get_json()
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO evacuation_routes
            (title, disaster_type, location_name, description,
            map_url, latitude, longitude, safe_zone,
            distance_km, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data['title'], data['disaster_type'],
            data['location_name'], data['description'],
            data['map_url'], data.get('latitude', 0),
            data.get('longitude', 0), data['safe_zone'],
            data['distance_km'], current_user['id']
        ))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Route added!'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/evacuation/<int:route_id>', methods=['DELETE'])
@jwt_required()
def delete_evacuation_route(route_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM evacuation_routes WHERE id=%s", (route_id,)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Route deleted!'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── AI CHATBOT ROUTE ──────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat_with_ai():
    try:
        data         = request.get_json()
        user_message = data.get('message', '')
        chat_history = data.get('history', [])
        if not user_message:
            return jsonify({'message': 'No message provided'}), 400
        response = get_ai_response(user_message, chat_history)
        return jsonify({
            'response': response['message'],
            'success' : response['success']
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── ACTIVITY ROUTES ──────────────────────────────────────────

@app.route('/api/activities', methods=['GET'])
@jwt_required()
def get_activities():
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM activities
            WHERE student_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """, (current_user['id'],))
        activities = cursor.fetchall()
        for a in activities:
            if hasattr(a.get('created_at'), 'isoformat'):
                a['created_at'] = a['created_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(activities), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/activities', methods=['POST'])
@jwt_required()
def add_activity():
    current_user = json.loads(get_jwt_identity())
    data = request.get_json()
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO activities
            (student_id, activity_type, title,
            description, score, percentage)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            current_user['id'],
            data.get('activity_type'),
            data.get('title'),
            data.get('description', ''),
            data.get('score', None),
            data.get('percentage', None)
        ))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Activity logged!'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── BADGE ROUTES ──────────────────────────────────────────

@app.route('/api/badges', methods=['GET'])
@jwt_required()
def get_my_badges():
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, sb.earned_at
            FROM student_badges sb
            JOIN badges b ON sb.badge_id = b.id
            WHERE sb.student_id = %s
            ORDER BY sb.earned_at DESC
        """, (current_user['id'],))
        badges = cursor.fetchall()
        for b in badges:
            if hasattr(b.get('earned_at'), 'isoformat'):
                b['earned_at'] = b['earned_at'].isoformat()

        cursor.execute("SELECT * FROM badges")
        all_badges = cursor.fetchall()
        earned_ids = {b['id'] for b in badges}
        locked     = [b for b in all_badges
                      if b['id'] not in earned_ids]

        cursor.close()
        db.close()
        return jsonify({
            'earned'      : badges,
            'locked'      : locked,
            'total_earned': len(badges),
            'total_badges': len(all_badges)
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/badges/check', methods=['POST'])
@jwt_required()
def check_badges():
    current_user = json.loads(get_jwt_identity())
    new_badges   = check_and_award_badges(current_user['id'])
    return jsonify({
        'new_badges': new_badges,
        'count'     : len(new_badges)
    }), 200


# ─── EMERGENCY CONTACT ROUTES ──────────────────────────────

@app.route('/api/emergency-contacts', methods=['GET'])
@jwt_required()
def get_emergency_contacts():
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM emergency_contacts
            WHERE student_id = %s
            ORDER BY is_primary DESC, created_at ASC
        """, (current_user['id'],))
        contacts = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(contacts), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/emergency-contacts', methods=['POST'])
@jwt_required()
def add_emergency_contact():
    current_user = json.loads(get_jwt_identity())
    data = request.get_json()
    try:
        db = get_db()
        cursor = db.cursor()
        if data.get('is_primary'):
            cursor.execute("""
                UPDATE emergency_contacts
                SET is_primary = FALSE
                WHERE student_id = %s
            """, (current_user['id'],))
        cursor.execute("""
            INSERT INTO emergency_contacts
            (student_id, name, relationship,
            phone, email, is_primary)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            current_user['id'], data['name'],
            data['relationship'], data['phone'],
            data.get('email', ''),
            data.get('is_primary', False)
        ))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Contact added!'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/emergency-contacts/<int:contact_id>',
           methods=['DELETE'])
@jwt_required()
def delete_emergency_contact(contact_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM emergency_contacts WHERE id = %s",
            (contact_id,)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Contact deleted!'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/sos', methods=['POST'])
@jwt_required()
def send_sos():
    current_user = json.loads(get_jwt_identity())
    data = request.get_json()
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO sos_alerts (student_id, message, location)
            VALUES (%s, %s, %s)
        """, (
            current_user['id'],
            data.get('message', 'EMERGENCY SOS!'),
            data.get('location', 'Unknown')
        ))
        db.commit()

        cursor2 = db.cursor(dictionary=True)
        cursor2.execute(
            "SELECT * FROM users WHERE id = %s",
            (current_user['id'],)
        )
        student = cursor2.fetchone()

        cursor2.execute("""
            SELECT * FROM emergency_contacts
            WHERE student_id = %s
        """, (current_user['id'],))
        contacts = cursor2.fetchall()

        cursor2.execute(
            "SELECT email, full_name, phone FROM users "
            "WHERE role='teacher'"
        )
        teachers = cursor2.fetchall()
        cursor2.close()
        cursor.close()
        db.close()

        sos_message = (
            f"SOS EMERGENCY ALERT\n\n"
            f"Student : {student['full_name']}\n"
            f"Phone   : {student.get('phone', 'N/A')}\n"
            f"Message : {data.get('message', 'EMERGENCY!')}\n"
            f"Location: {data.get('location', 'Unknown')}\n"
            f"Time    : "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Please respond immediately!\n\n"
            f"Emergency: 112 | Police: 100 | Ambulance: 102"
        )

        def send_sos_notifications():
            for teacher in teachers:
                try:
                    send_email(
                        teacher['email'],
                        f"SOS ALERT from {student['full_name']}!",
                        sos_message
                    )
                except Exception as e:
                    print(f"SOS teacher email error: {e}")
                if teacher.get('phone'):
                    send_sms_safe(
                        teacher['phone'],
                        f"SOS! {student['full_name']} needs help!\n"
                        f"{data.get('message', 'EMERGENCY!')}\n"
                        f"Call: {student.get('phone', 'N/A')}\n"
                        f"Emergency: 112"
                    )

            for contact in contacts:
                try:
                    if contact.get('email'):
                        send_email(
                            contact['email'],
                            f"SOS from {student['full_name']}!",
                            sos_message
                        )
                    if contact.get('phone'):
                        send_sms_safe(
                            contact['phone'],
                            f"SOS ALERT! "
                            f"{student['full_name']} needs help!\n"
                            f"{data.get('message', 'EMERGENCY!')}\n"
                            f"Location: "
                            f"{data.get('location', 'Unknown')}\n"
                            f"Call: {student.get('phone', 'N/A')}\n"
                            f"Emergency: 112"
                        )
                except Exception as e:
                    print(f"SOS contact error: {e}")

            if student.get('phone'):
                send_sms_safe(
                    student['phone'],
                    f"Your SOS sent to {len(contacts)} contacts "
                    f"and {len(teachers)} teachers. "
                    f"Help is on the way! Emergency: 112"
                )

        thread = threading.Thread(target=send_sos_notifications)
        thread.daemon = True
        thread.start()

        return jsonify({
            'message'          : 'SOS sent successfully!',
            'contacts_alerted' : len(contacts),
            'teachers_alerted' : len(teachers)
        }), 201

    except Exception as e:
        print(f"SOS error: {e}")
        return jsonify({'message': str(e)}), 500


# ─── TEACHER EMERGENCY ROUTES ──────────────────────────────

@app.route('/api/teacher/students-contacts', methods=['GET'])
@jwt_required()
def get_students_with_contacts():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.full_name, u.email, u.phone,
            COUNT(ec.id) as contact_count
            FROM users u
            LEFT JOIN emergency_contacts ec ON u.id = ec.student_id
            WHERE u.role = 'student'
            GROUP BY u.id, u.full_name, u.email, u.phone
            ORDER BY u.full_name ASC
        """)
        students = cursor.fetchall()

        result = []
        for student in students:
            cursor2 = db.cursor(dictionary=True)
            cursor2.execute("""
                SELECT * FROM emergency_contacts
                WHERE student_id = %s
                ORDER BY is_primary DESC
            """, (student['id'],))
            contacts = cursor2.fetchall()
            cursor2.close()
            student['contacts'] = contacts
            result.append(student)

        cursor.close()
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/teacher/send-targeted-alert', methods=['POST'])
@jwt_required()
def send_targeted_alert():
    current_user = json.loads(get_jwt_identity())
    data = request.get_json()
    try:
        title            = data.get('title', '').strip()
        message          = data.get('message', '').strip()
        disaster_type    = data.get('disaster_type', 'General')
        student_ids      = data.get('student_ids', [])
        include_contacts = data.get('include_contacts', True)

        if not title:
            return jsonify({'message': 'Title is required'}), 400
        if not message:
            return jsonify({'message': 'Message is required'}), 400
        if not student_ids:
            return jsonify({
                'message': 'Select at least one student'
            }), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO alerts
            (title, message, disaster_type, created_by)
            VALUES (%s, %s, %s, %s)
        """, (title, message, disaster_type, current_user['id']))
        db.commit()

        format_ids = ','.join(['%s'] * len(student_ids))
        cursor2 = db.cursor(dictionary=True)
        cursor2.execute(f"""
            SELECT id, full_name, email, phone
            FROM users
            WHERE id IN ({format_ids}) AND role = 'student'
        """, tuple(student_ids))
        students = cursor2.fetchall()
        cursor2.close()
        cursor.close()
        db.close()

        def send_targeted_notifications():
            emails_sent   = 0
            contacts_sent = 0

            for student in students:
                try:
                    if student.get('email'):
                        send_email(
                            student['email'],
                            f"URGENT ALERT: {title}",
                            f"""DISASTER ALERT NOTIFICATION

Type    : {disaster_type}
Alert   : {title}

Message : {message}

Stay safe and follow all safety instructions!

Emergency: 112 | Fire: 101 | Ambulance: 102 | Police: 100

Disaster Preparedness System"""
                        )
                        emails_sent += 1

                    if student.get('phone'):
                        send_sms_safe(
                            student['phone'],
                            f"URGENT ALERT: {title}\n"
                            f"Type: {disaster_type}\n"
                            f"{message}\nEmergency: 112"
                        )

                except Exception as e:
                    print(f"Student alert error: {e}")

                if include_contacts:
                    try:
                        db3 = get_db()
                        cur3 = db3.cursor(dictionary=True)
                        cur3.execute("""
                            SELECT * FROM emergency_contacts
                            WHERE student_id = %s
                        """, (student['id'],))
                        contacts = cur3.fetchall()
                        cur3.close()
                        db3.close()

                        for contact in contacts:
                            try:
                                if contact.get('email'):
                                    send_email(
                                        contact['email'],
                                        f"ALERT for "
                                        f"{student['full_name']}: "
                                        f"{title}",
                                        f"""DISASTER ALERT

Dear {contact['name']},

{student['full_name']} received a disaster alert.

Type   : {disaster_type}
Alert  : {title}
Message: {message}

Student Phone: {student.get('phone', 'N/A')}
Emergency: 112

Stay Safe!"""
                                    )
                                    contacts_sent += 1

                                if contact.get('phone'):
                                    send_sms_safe(
                                        contact['phone'],
                                        f"ALERT for "
                                        f"{student['full_name']}!\n"
                                        f"Type: {disaster_type}\n"
                                        f"{title}\n"
                                        f"Student: "
                                        f"{student.get('phone','N/A')}\n"
                                        f"Emergency: 112"
                                    )
                            except Exception as e:
                                print(f"Contact alert error: {e}")
                    except Exception as e:
                        print(f"Contacts fetch error: {e}")

            print(f"Targeted alert done! "
                  f"Students:{emails_sent} "
                  f"Contacts:{contacts_sent}")

        thread = threading.Thread(
            target=send_targeted_notifications
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'message'           : 'Targeted alert sent!',
            'students_notified' : len(students),
            'include_contacts'  : include_contacts
        }), 201

    except Exception as e:
        print(f"Targeted alert error: {e}")
        return jsonify({'message': str(e)}), 500


@app.route('/api/sos/all', methods=['GET'])
@jwt_required()
def get_all_sos():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, u.full_name, u.email, u.phone
            FROM sos_alerts s
            JOIN users u ON s.student_id = u.id
            ORDER BY s.created_at DESC
        """)
        sos_list = cursor.fetchall()
        for s in sos_list:
            if hasattr(s.get('created_at'), 'isoformat'):
                s['created_at'] = s['created_at'].isoformat()
        cursor.close()
        db.close()
        return jsonify(sos_list), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/sos/<int:sos_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_sos(sos_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE sos_alerts SET status = 'resolved' "
            "WHERE id = %s", (sos_id,)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'SOS resolved!'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500



# ─── FORGOT PASSWORD ROUTES ──────────────────────────────

import random
import string

def generate_otp():
    """Generate 6 digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(to_email, otp, full_name):
    """Send OTP email with beautiful template"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        GMAIL        = 'kavyaghanapuram@gmail.com'
        APP_PASSWORD = 'amux kqop mrtb mndz'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Password Reset OTP - Disaster Prep System'
        msg['From']    = f"Disaster Prep System <{GMAIL}>"
        msg['To']      = to_email

        html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
</head>
<body style="font-family:Arial,sans-serif;
  background:#f5f5f5;padding:20px;margin:0">
<div style="max-width:500px;margin:0 auto;
  background:white;border-radius:16px;
  overflow:hidden;
  box-shadow:0 4px 20px rgba(0,0,0,0.1)">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#e94560);
    padding:30px;text-align:center">
    <div style="font-size:48px;margin-bottom:8px">🌪️</div>
    <h1 style="color:white;margin:0;font-size:22px">
      Disaster Prep System
    </h1>
    <p style="color:rgba(255,255,255,0.7);
      margin:6px 0 0;font-size:13px">
      Password Reset Request
    </p>
  </div>

  <!-- Body -->
  <div style="padding:32px">
    <h2 style="color:#1a1a2e;margin:0 0 12px;font-size:20px">
      Hello, {full_name}! 👋
    </h2>
    <p style="color:#555;font-size:14px;
      line-height:1.6;margin:0 0 24px">
      We received a request to reset your password.
      Use the OTP below to reset it.
      This OTP is valid for <strong>10 minutes</strong>.
    </p>

    <!-- OTP Box -->
    <div style="background:linear-gradient(135deg,#1a1a2e,#2c3e50);
      border-radius:12px;padding:24px;
      text-align:center;margin:0 0 24px">
      <p style="color:rgba(255,255,255,0.6);
        font-size:12px;margin:0 0 8px;
        letter-spacing:2px;text-transform:uppercase">
        Your OTP Code
      </p>
      <div style="display:inline-block">
        <span style="font-size:42px;font-weight:900;
          color:#e94560;letter-spacing:10px;
          text-shadow:0 0 20px rgba(233,69,96,0.5)">
          {otp}
        </span>
      </div>
      <p style="color:rgba(255,255,255,0.4);
        font-size:11px;margin:10px 0 0">
        ⏰ Valid for 10 minutes only
      </p>
    </div>

    <!-- Warning -->
    <div style="background:#fff3cd;border-radius:8px;
      padding:14px 16px;margin:0 0 20px;
      border-left:4px solid #f39c12">
      <p style="color:#856404;font-size:13px;margin:0;
        font-weight:600">
        ⚠️ Security Notice
      </p>
      <p style="color:#856404;font-size:12px;
        margin:4px 0 0;line-height:1.5">
        If you did not request a password reset,
        please ignore this email.
        Your account is still secure.
      </p>
    </div>

    <p style="color:#999;font-size:12px;
      text-align:center;margin:0">
      Do not share this OTP with anyone.
      Our team will never ask for your OTP.
    </p>
  </div>

  <!-- Footer -->
  <div style="background:#1a1a2e;padding:16px;
    text-align:center">
    <p style="color:rgba(255,255,255,0.4);
      font-size:11px;margin:0">
      🛡️ Be Prepared • Stay Safe • Save Lives
    </p>
  </div>
</div>
</body>
</html>"""

        plain_text = f"""
Hello {full_name},

Your OTP for password reset is: {otp}

This OTP is valid for 10 minutes only.

If you did not request this, please ignore this email.

Disaster Prep System
        """

        msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(GMAIL, APP_PASSWORD)
        server.sendmail(GMAIL, to_email, msg.as_bytes())
        server.quit()
        print(f"OTP email sent to: {to_email}")
        return True

    except Exception as e:
        print(f"OTP email error: {e}")
        return False


@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data  = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({
                'message': 'Email is required!'
            }), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, full_name, email FROM users "
            "WHERE email = %s", (email,)
        )
        user = cursor.fetchone()

        if not user:
            # Don't reveal if email exists
            return jsonify({
                'message': 'If this email exists, '
                           'OTP has been sent!'
            }), 200

        # Delete old OTPs for this email
        cursor.execute(
            "DELETE FROM password_resets WHERE email = %s",
            (email,)
        )

        # Generate new OTP
        otp        = generate_otp()
        expires_at = datetime.now().replace(microsecond=0)
        from datetime import timedelta
        expires_at = expires_at + timedelta(minutes=10)

        # Save OTP to database
        cursor2 = db.cursor()
        cursor2.execute("""
            INSERT INTO password_resets
            (email, otp, expires_at)
            VALUES (%s, %s, %s)
        """, (email, otp, expires_at))
        db.commit()
        cursor.close()
        cursor2.close()
        db.close()

        # Send OTP email in background
        def send_otp():
            send_otp_email(
                user['email'], otp, user['full_name']
            )

        thread = threading.Thread(target=send_otp)
        thread.daemon = True
        thread.start()

        print(f"OTP generated for {email}: {otp}")
        return jsonify({
            'message': 'OTP sent to your email! '
                      'Check your inbox.',
            'email'  : email
        }), 200

    except Exception as e:
        print(f"Forgot password error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500


@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data  = request.get_json()
        email = data.get('email', '').strip().lower()
        otp   = data.get('otp', '').strip()

        if not email or not otp:
            return jsonify({
                'message': 'Email and OTP are required!'
            }), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM password_resets
            WHERE email = %s
            AND otp = %s
            AND used = FALSE
            AND expires_at > NOW()
            ORDER BY created_at DESC
            LIMIT 1
        """, (email, otp))
        reset = cursor.fetchone()
        cursor.close()
        db.close()

        if not reset:
            return jsonify({
                'message': 'Invalid or expired OTP! '
                          'Please try again.'
            }), 400

        return jsonify({
            'message': 'OTP verified successfully!',
            'valid'  : True
        }), 200

    except Exception as e:
        print(f"Verify OTP error: {e}")
        return jsonify({'message': str(e)}), 500


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data         = request.get_json()
        email        = data.get('email', '').strip().lower()
        otp          = data.get('otp', '').strip()
        new_password = data.get('new_password', '').strip()

        if not email or not otp or not new_password:
            return jsonify({
                'message': 'All fields are required!'
            }), 400

        if len(new_password) < 6:
            return jsonify({
                'message': 'Password must be at least 6 characters!'
            }), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Verify OTP again
        cursor.execute("""
            SELECT * FROM password_resets
            WHERE email = %s
            AND otp = %s
            AND used = FALSE
            AND expires_at > NOW()
            ORDER BY created_at DESC
            LIMIT 1
        """, (email, otp))
        reset = cursor.fetchone()

        if not reset:
            cursor.close()
            db.close()
            return jsonify({
                'message': 'Invalid or expired OTP!'
            }), 400

        # Hash new password
        hashed = bcrypt.generate_password_hash(
            new_password
        ).decode('utf-8')

        # Update password
        cursor2 = db.cursor()
        cursor2.execute("""
            UPDATE users SET password = %s
            WHERE email = %s
        """, (hashed, email))

        # Mark OTP as used
        cursor2.execute("""
            UPDATE password_resets SET used = TRUE
            WHERE email = %s AND otp = %s
        """, (email, otp))

        db.commit()

        # Get user details for confirmation email
        cursor.execute(
            "SELECT full_name FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        cursor2.close()
        db.close()

        # Send confirmation email
        def send_confirmation():
            try:
                send_email(
                    email,
                    'Password Reset Successful!',
                    f"""Dear {user['full_name']},

Your password has been reset successfully!

You can now login with your new password.

If you did not make this change please
contact us immediately!

Time: {datetime.now().strftime('%d %B %Y at %I:%M %p')}

Stay Safe!
Disaster Prep System"""
                )
            except Exception as e:
                print(f"Confirmation email error: {e}")

        thread = threading.Thread(target=send_confirmation)
        thread.daemon = True
        thread.start()

        print(f"Password reset successful for: {email}")
        return jsonify({
            'message': 'Password reset successful! '
                      'You can now login.'
        }), 200

    except Exception as e:
        print(f"Reset password error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500


@app.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    try:
        data  = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({
                'message': 'Email is required!'
            }), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, full_name FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({
                'message': 'Email not found!'
            }), 404

        # Delete old OTPs
        cursor2 = db.cursor()
        cursor2.execute(
            "DELETE FROM password_resets WHERE email = %s",
            (email,)
        )

        # Generate new OTP
        otp        = generate_otp()
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(minutes=10)

        cursor2.execute("""
            INSERT INTO password_resets
            (email, otp, expires_at)
            VALUES (%s, %s, %s)
        """, (email, otp, expires_at))
        db.commit()
        cursor.close()
        cursor2.close()
        db.close()

        def send_new_otp():
            send_otp_email(
                email, otp, user['full_name']
            )

        thread = threading.Thread(target=send_new_otp)
        thread.daemon = True
        thread.start()

        print(f"OTP resent for {email}: {otp}")
        return jsonify({
            'message': 'New OTP sent to your email!'
        }), 200

    except Exception as e:
        print(f"Resend OTP error: {e}")
        return jsonify({'message': str(e)}), 500

# ─── NEARBY DISASTER CALCULATION ──────────────────────────────

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km using Haversine formula"""
    R    = 6371
    lat1 = math.radians(float(lat1))
    lat2 = math.radians(float(lat2))
    lon1 = math.radians(float(lon1))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (math.sin(dlat/2)**2 +
         math.cos(lat1) * math.cos(lat2) *
         math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return round(R * c, 2)


@app.route('/api/nearby-resources', methods=['POST'])
@jwt_required()
def get_nearby_resources():
    try:
        data = request.get_json()
        user_lat  = float(data.get('latitude',  17.3850))
        user_lon  = float(data.get('longitude', 78.4867))
        radius_km = float(data.get('radius', 10))

        # Fetch evacuation routes from DB
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, u.full_name as created_by_name
            FROM evacuation_routes e
            JOIN users u ON e.created_by = u.id
            WHERE e.latitude != 0 AND e.longitude != 0
        """)
        routes = cursor.fetchall()
        cursor.close()
        db.close()

        # Calculate distance for each route
        nearby = []
        for route in routes:
            try:
                dist = calculate_distance(
                    user_lat, user_lon,
                    route['latitude'], route['longitude']
                )
                if dist <= radius_km:
                    route_data = dict(route)
                    if hasattr(route_data.get('created_at'),
                               'isoformat'):
                        route_data['created_at'] = \
                            route_data['created_at'].isoformat()
                    route_data['distance_from_user'] = dist
                    route_data['direction'] = get_direction(
                        user_lat, user_lon,
                        route['latitude'], route['longitude']
                    )
                    nearby.append(route_data)
            except Exception as e:
                print(f"Distance calc error: {e}")

        # Sort by distance
        nearby.sort(key=lambda x: x['distance_from_user'])

        # Risk assessment based on location
        risk_level = assess_risk(user_lat, user_lon)

        return jsonify({
            'success'   : True,
            'user_location': {
                'latitude' : user_lat,
                'longitude': user_lon
            },
            'radius_km'   : radius_km,
            'nearby_count': len(nearby),
            'resources'   : nearby,
            'risk_level'  : risk_level
        }), 200

    except Exception as e:
        print(f"Nearby resources error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def get_direction(lat1, lon1, lat2, lon2):
    """Get compass direction from point 1 to point 2"""
    try:
        dlat = float(lat2) - float(lat1)
        dlon = float(lon2) - float(lon1)
        angle = math.degrees(math.atan2(dlon, dlat))
        if angle < 0:
            angle += 360
        dirs = ['N','NE','E','SE','S','SW','W','NW']
        idx  = round(angle / 45) % 8
        return dirs[idx]
    except:
        return 'N'


def assess_risk(lat, lon):
    """Basic risk assessment based on location"""
    # This is a simplified assessment
    # In production connect to real disaster APIs
    return {
        'level'      : 'Medium',
        'color'      : '#f39c12',
        'description': 'Stay alert and be prepared',
        'tips'       : [
            'Keep emergency kit ready',
            'Know your evacuation route',
            'Save emergency contacts',
            'Monitor local weather alerts'
        ]
    }


@app.route('/api/calculate-safe-distance', methods=['POST'])
@jwt_required()
def calculate_safe_distance():
    try:
        data     = request.get_json()
        user_lat = float(data.get('latitude',  17.3850))
        user_lon = float(data.get('longitude', 78.4867))

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM evacuation_routes
            WHERE latitude != 0 AND longitude != 0
        """)
        routes = cursor.fetchall()
        cursor.close()
        db.close()

        results = []
        for route in routes:
            try:
                dist = calculate_distance(
                    user_lat, user_lon,
                    route['latitude'], route['longitude']
                )
                results.append({
                    'id'          : route['id'],
                    'title'       : route['title'],
                    'disaster_type': route['disaster_type'],
                    'safe_zone'   : route['safe_zone'],
                    'distance_km' : dist,
                    'direction'   : get_direction(
                        user_lat, user_lon,
                        route['latitude'], route['longitude']
                    ),
                    'latitude'    : route['latitude'],
                    'longitude'   : route['longitude'],
                    'map_url'     : route['map_url']
                })
            except Exception as e:
                print(f"Route calc error: {e}")

        results.sort(key=lambda x: x['distance_km'])

        return jsonify({
            'success'       : True,
            'user_location' : {
                'latitude' : user_lat,
                'longitude': user_lon
            },
            'safe_zones'    : results,
            'nearest'       : results[0] if results else None
        }), 200

    except Exception as e:
        print(f"Safe distance error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
# ─── RUN ──────────────────────────────────────────

if __name__ == '__main__':
    print("="*50)
    print("Flask server starting...")
    print("Web    : http://127.0.0.1:5000")
    print("Mobile : http://192.168.29.112:5000")
    print("="*50)
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')