from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data.get('username') == 'admin' and data.get('password') == 'password':
        return jsonify({"token": "valid-token-123"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/verify', methods=['GET'])
def verify():
    auth_header = request.headers.get('Authorization')
    if auth_header == "Bearer valid-token-123":
        return jsonify({"status": "verified"}), 200
    return jsonify({"error": "Unauthorized"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)