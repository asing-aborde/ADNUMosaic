from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()
app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'adnu-mosaic-secret-2026')
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'adnu_mosaic')
    )

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id FROM USER WHERE email = %s", (data['email'],))
    if cur.fetchone():
        cur.close()
        db.close()
        return jsonify({'error': 'An account with this email already exists.'}), 409
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    cur.execute("""
        INSERT INTO USER (email, password, first_name, last_name, user_type, year_level)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (data['email'], hashed, data['first_name'], data['last_name'],
          data['user_type'], data['year_level']))
    db.commit()
    cur.close()
    db.close()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM USER WHERE email = %s", (data['email'],))
    user = cur.fetchone()
    cur.close()
    db.close()
    if not user or not bcrypt.check_password_hash(user[2], data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_access_token(identity=user[0])
    return jsonify({'token': token, 'first_name': user[3]}), 200

@app.route('/api/pins', methods=['GET'])
def get_pins():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT p.pin_id, p.title, p.content, l.location_name,
               u.first_name, u.last_name, p.created_at
        FROM PINS p
        JOIN LOCATION l ON p.location_id = l.location_id
        JOIN USER u ON p.user_id = u.user_id
        WHERE p.is_public = 1
        ORDER BY p.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    db.close()
    pins = [{'pin_id': r[0], 'title': r[1], 'content': r[2],
             'location': r[3], 'author': f"{r[4]} {r[5]}", 'date': str(r[6])}
            for r in rows]
    return jsonify(pins), 200

if __name__ == '__main__':
    app.run(debug=True)