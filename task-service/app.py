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
    # Fix: Add charset='utf8mb4' to handle emojis and special characters correctly
    return mysql.connector.connect(
        host=DB_HOST, 
        user='root', 
        password='password', 
        database='tasks_db',
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

def check_auth():
    auth_resp = requests.get(AUTH_URL, headers={"Authorization": request.headers.get('Authorization')})
    return auth_resp.status_code == 200

@app.route('/tasks', methods=['GET', 'POST'])
def handle_tasks():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    # Fix: Ensure the cursor reads/writes UTF-8 properly
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        data = request.json
        
        # Fix: Convert empty string date to None (NULL in SQL) so it doesn't break
        deadline_val = data.get('deadline')
        if not deadline_val or deadline_val == "":
            deadline_val = None

        sql = "INSERT INTO tasks (title, description, deadline, urgency, status) VALUES (%s, %s, %s, %s, 'NEW')"
        val = (data['title'], data.get('description', ''), deadline_val, data.get('urgency', 'Low'))
        
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"message": "Task created"}), 201

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    
    # Format date for JSON
    for t in tasks:
        if t['deadline']:
            t['deadline'] = str(t['deadline'])
            
    conn.close()
    return jsonify(tasks)

@app.route('/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
def update_delete_task(task_id):
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'DELETE':
        cursor.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Task deleted"}), 200

    if request.method == 'PUT':
        data = request.json
        
        # Handle simple drag-and-drop status update
        if 'status' in data and len(data) == 1:
            cursor.execute("UPDATE tasks SET status=%s WHERE id=%s", (data['status'], task_id))
        
        # Handle Full Edit (Popup)
        else:
            deadline_val = data.get('deadline')
            if not deadline_val or deadline_val == "":
                deadline_val = None
                
            sql = "UPDATE tasks SET title=%s, description=%s, deadline=%s, urgency=%s WHERE id=%s"
            val = (data['title'], data.get('description'), deadline_val, data.get('urgency'), task_id)
            cursor.execute(sql, val)

        conn.commit()
        conn.close()
        return jsonify({"message": "Task updated"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)