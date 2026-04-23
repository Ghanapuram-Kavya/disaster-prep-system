from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import get_db
from email_service import init_mail, send_alert_email, send_quiz_result_email, send_welcome_email
from flask_mail import Mail
import json

app = Flask(__name__)
init_mail(app)
CORS(app)
bcrypt = Bcrypt(app)

app.config['JWT_SECRET_KEY'] = 'disaster_prep_secret_key_2024'
jwt = JWTManager(app)

# ─── AUTH ROUTES ────────────────────────────────────────────

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([full_name, email, password, role]):
        return jsonify({'message': 'All fields are required'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, %s)",
            (full_name, email, hashed_password, role)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        return jsonify({'message': 'Email already exists'}), 400


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            access_token = create_access_token(identity=json.dumps({
                'id': user['id'],
                'role': user['role'],
                'full_name': user['full_name']
            }))
            return jsonify({
                'token': access_token,
                'role': user['role'],
                'full_name': user['full_name'],
                'id': user['id']
            }), 200
        else:
            return jsonify({'message': 'Invalid email or password'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── LESSON ROUTES ────────────────────────────────────────────

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
            "INSERT INTO lessons (title, topic, content, video_url, created_by) VALUES (%s, %s, %s, %s, %s)",
            (data['title'], data['topic'], data['content'], data['video_url'], current_user['id'])
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Lesson added successfully'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>', methods=['DELETE'])
@jwt_required()
def delete_lesson(lesson_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Lesson deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── QUIZ ROUTES ────────────────────────────────────────────

@app.route('/api/quizzes/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_quizzes(lesson_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quizzes WHERE lesson_id = %s", (lesson_id,))
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
            (lesson_id, question, option_a, option_b, option_c, option_d, correct_option) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (data['lesson_id'], data['question'], data['option_a'],
             data['option_b'], data['option_c'], data['option_d'], data['correct_option'])
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Quiz added successfully'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── RESULTS ROUTES ────────────────────────────────────────────

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
            """INSERT INTO results (student_id, lesson_id, score, total_questions, percentage) 
            VALUES (%s, %s, %s, %s, %s)""",
            (current_user['id'], data['lesson_id'], data['score'],
             data['total_questions'], percentage)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Result saved', 'percentage': percentage}), 201
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
        cursor.close()
        db.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── ALERTS ROUTES ────────────────────────────────────────────

@app.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        alerts = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/alerts', methods=['POST'])
@jwt_required()
def add_alert():
    data = request.get_json()
    current_user = json.loads(get_jwt_identity())
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO alerts (title, message, disaster_type, created_by) VALUES (%s, %s, %s, %s)",
            (data['title'], data['message'], data['disaster_type'], current_user['id'])
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Alert created successfully'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── LEADERBOARD ROUTE ────────────────────────────────────────────

@app.route('/api/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.full_name, 
                   COUNT(r.id) as quizzes_taken,
                   AVG(r.percentage) as avg_percentage,
                   SUM(r.score) as total_score
            FROM results r
            JOIN users u ON r.student_id = u.id
            GROUP BY r.student_id, u.full_name
            ORDER BY avg_percentage DESC
            LIMIT 10
        """)
        leaderboard = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(leaderboard), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# ─── RUN APP ────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)