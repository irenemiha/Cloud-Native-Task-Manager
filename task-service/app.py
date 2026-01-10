from flask import Flask, request, jsonify
import mysql.connector
import requests
import os

app = Flask(__name__)

# Configurare DB luată din variabile de mediu (pt Kubernetes)
DB_HOST = os.getenv('DB_HOST', 'localhost')
AUTH_URL = os.getenv('AUTH_URL', 'http://auth-service:5001/verify')

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST, user='root', password='password', database='tasks_db'
    )

@app.route('/tasks', methods=['GET', 'POST'])
def handle_tasks():
    # 1. Verificare Autentificare (Comunicare între microservicii)
    auth_resp = requests.get(AUTH_URL, headers={"Authorization": request.headers.get('Authorization')})
    if auth_resp.status_code != 200:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        title = request.json.get('title')
        cursor.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))
        conn.commit()
        return jsonify({"message": "Task created"}), 201

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    return jsonify(tasks)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)