from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import uuid
import hashlib

app = Flask(__name__)
CORS(app)

# Database Connection Config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_CONFIG = {
    'host': DB_HOST,
    'user': 'root',
    'password': 'password',
    'database': 'tasks_db',
    'charset': 'utf8mb4'
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"error": "Username already exists"}), 409
            
        # Create user
        hashed = hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
        conn.commit()
        return jsonify({"message": "User created"}), 201
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    hashed = hash_password(password)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, hashed))
        user = cursor.fetchone()
        
        if user:
            # Generate Token
            token = str(uuid.uuid4())
            cursor.execute("INSERT INTO tokens (token, user_id) VALUES (%s, %s)", (token, user['id']))
            conn.commit()
            return jsonify({"token": token}), 200
            
        return jsonify({"error": "Invalid credentials"}), 401
    finally:
        conn.close()

@app.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tokens WHERE token = %s", (token,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Logged out"}), 200

@app.route('/verify', methods=['GET'])
def verify():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM tokens WHERE token = %s", (token,))
        result = cursor.fetchone()
        
        if result:
            return jsonify({"status": "verified", "user_id": result['user_id']}), 200
        return jsonify({"error": "Unauthorized"}), 401
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)