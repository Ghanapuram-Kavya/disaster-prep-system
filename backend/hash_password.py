from flask_bcrypt import Bcrypt

app_bcrypt = Bcrypt()

teacher_hash = app_bcrypt.generate_password_hash('teacher123').decode('utf-8')
student_hash = app_bcrypt.generate_password_hash('student123').decode('utf-8')

print("="*60)
print(f"Teacher hash:\n{teacher_hash}")
print("="*60)
print(f"Student hash:\n{student_hash}")
print("="*60)