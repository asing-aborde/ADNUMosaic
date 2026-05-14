from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()
app = Flask(__name__)
CORS(app)

def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'adnu_mosaic')
    )

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