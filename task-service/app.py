from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import requests
import os

app = Flask(__name__)
CORS(app)

DB_HOST = os.getenv('DB_HOST', 'localhost')
AUTH_URL = os.getenv('AUTH_URL', 'http://auth-service:5001/verify')

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST, user='root', password='password', database='tasks_db',
        charset='utf8mb4', collation='utf8mb4_unicode_ci'
    )

def get_user_id():
    # Call Auth Service to check token AND get User ID
    try:
        auth_resp = requests.get(AUTH_URL, headers={"Authorization": request.headers.get('Authorization')})
        if auth_resp.status_code == 200:
            return auth_resp.json().get('user_id')
    except:
        return None
    return None

@app.route('/tasks', methods=['GET', 'POST'])
def handle_tasks():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        data = request.json
        deadline_val = data.get('deadline')
        if not deadline_val or deadline_val == "":
            deadline_val = None

        # save with user_id
        sql = "INSERT INTO tasks (title, description, deadline, urgency, status, user_id) VALUES (%s, %s, %s, %s, 'NEW', %s)"
        val = (data['title'], data.get('description', ''), deadline_val, data.get('urgency', 'Low'), user_id)
        
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return jsonify({"message": "Task created"}), 201

    # Filter by user_id
    cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (user_id,))
    tasks = cursor.fetchall()
    
    for t in tasks:
        if t['deadline']:
            t['deadline'] = str(t['deadline'])
            
    conn.close()
    return jsonify(tasks)

@app.route('/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
def update_delete_task(task_id):
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'DELETE':
        # Ensure user owns task
        cursor.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (task_id, user_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Task deleted"}), 200

    if request.method == 'PUT':
        data = request.json
        
        # Only allow update if task belongs to user
        if 'status' in data and len(data) == 1:
            cursor.execute("UPDATE tasks SET status=%s WHERE id=%s AND user_id=%s", (data['status'], task_id, user_id))
        else:
            deadline_val = data.get('deadline')
            if not deadline_val or deadline_val == "":
                deadline_val = None
            sql = "UPDATE tasks SET title=%s, description=%s, deadline=%s, urgency=%s WHERE id=%s AND user_id=%s"
            val = (data['title'], data.get('description'), deadline_val, data.get('urgency'), task_id, user_id)
            cursor.execute(sql, val)

        conn.commit()
        conn.close()
        return jsonify({"message": "Task updated"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)