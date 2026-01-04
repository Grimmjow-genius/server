from flask import Flask, request, jsonify
import os, sqlite3, requests, re
from datetime import datetime, timedelta
from threading import Lock

app = Flask(__name__)
db_lock = Lock()

AUTHORIZED_USERS = set(os.getenv("AUTHORIZED_USERS", "").split(","))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_CHAT_ID")

def init_db():
    with sqlite3.connect('tasks.db', timeout=10) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS tasks 
                       (id INTEGER PRIMARY KEY, user_id TEXT, card TEXT, template TEXT, 
                        result TEXT, created_at TIMESTAMP)''')
init_db()

@app.route('/authorize_task', methods=['POST'])
def authorize():
    data = request.json
    user_id = data.get('user_id')
    
    if user_id not in AUTHORIZED_USERS:
        return jsonify({'authorized': False})
    
    task_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    with db_lock, sqlite3.connect('tasks.db', timeout=10) as conn:
        conn.execute("INSERT INTO tasks (user_id, card, template, created_at) VALUES(?,?,?,?)",
                    (user_id, data['card'], data['template'], datetime.now()))
    
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                 data={'chat_id': ADMIN_ID, 'text': f"✅ Task #{task_id} | {user_id}\n{data['card'][-4:]} | {data['template']}"})
    
    return jsonify({'authorized': True, 'task_id': task_id})

@app.route('/report_hit/<task_id>', methods=['POST'])
def report_hit():
    data = request.json
    user_id = data['user_id']
    result = data['result']
    
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                 data={'chat_id': ADMIN_ID, 'text': f"🎉 HIT #{task_id}\n{result}"})
    
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)