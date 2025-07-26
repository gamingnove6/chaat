from flask import Flask, request, jsonify
from datetime import datetime
import threading

app = Flask(__name__)
messages = []  # In-memory message store
lock = threading.Lock()

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    if not data or 'user' not in data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    with lock:
        messages.append({
            'user': data['user'],
            'message': data['message'],
            'timestamp': datetime.utcnow().isoformat()
        })
    return jsonify({'status': 'Message sent'}), 200

@app.route('/messages', methods=['GET'])
def get_messages():
    last_index = int(request.args.get('last_index', 0))
    with lock:
        return jsonify({
            'messages': messages[last_index:],
            'last_index': len(messages)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
