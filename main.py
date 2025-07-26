from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)

# In-memory storage for messages (in production, use a database)
messages = []
message_lock = threading.Lock()

# Maximum number of messages to keep in memory
MAX_MESSAGES = 1000

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "Chat Server Running",
        "endpoints": {
            "send_message": "POST /send",
            "get_messages": "GET /messages",
            "get_new_messages": "GET /messages/since/<timestamp>"
        }
    })

@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'message' not in data:
            return jsonify({"error": "Username and message are required"}), 400
        
        username = data['username'].strip()
        message_text = data['message'].strip()
        
        if not username or not message_text:
            return jsonify({"error": "Username and message cannot be empty"}), 400
        
        # Create message object
        message = {
            "id": len(messages) + 1,
            "username": username,
            "message": message_text,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Thread-safe message addition
        with message_lock:
            messages.append(message)
            # Keep only the latest MAX_MESSAGES
            if len(messages) > MAX_MESSAGES:
                messages.pop(0)
        
        return jsonify({
            "status": "success",
            "message": "Message sent successfully",
            "data": message
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 100)  # Maximum 100 messages at once
        
        with message_lock:
            # Return the latest messages
            latest_messages = messages[-limit:] if messages else []
        
        return jsonify({
            "status": "success",
            "count": len(latest_messages),
            "messages": latest_messages
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/messages/since/<timestamp>', methods=['GET'])
def get_messages_since(timestamp):
    try:
        # Convert timestamp to datetime for comparison
        since_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        with message_lock:
            new_messages = []
            for msg in messages:
                msg_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                if msg_time > since_time:
                    new_messages.append(msg)
        
        return jsonify({
            "status": "success",
            "count": len(new_messages),
            "messages": new_messages
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/users/online', methods=['GET'])
def get_online_users():
    """Get list of users who sent messages in the last 5 minutes"""
    try:
        cutoff_time = datetime.utcnow().timestamp() - 300  # 5 minutes ago
        
        online_users = set()
        with message_lock:
            for msg in messages:
                msg_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00')).timestamp()
                if msg_time > cutoff_time:
                    online_users.add(msg['username'])
        
        return jsonify({
            "status": "success",
            "online_users": list(online_users),
            "count": len(online_users)
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
