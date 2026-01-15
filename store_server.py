import os
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['UPLOAD_FOLDER'] = 'shared_media'
app.config['DATABASE'] = 'database.db'

# Ensure upload folders exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'queue'), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            filename TEXT NOT NULL,
            type TEXT NOT NULL,
            size INTEGER,
            duration INTEGER DEFAULT 5,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            name TEXT,
            last_seen TIMESTAMP,
            status TEXT DEFAULT 'offline'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER,
            device_id TEXT,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY (media_id) REFERENCES media (id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/media', methods=['GET'])
def get_media():
    conn = get_db_connection()
    media = conn.execute('SELECT * FROM media').fetchall()
    conn.close()
    return jsonify([dict(m) for m in media])

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = file.filename
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
            folder = 'images'
            media_type = 'image'
        elif file_ext in ['mp4', 'avi', 'mov', 'mkv']:
            folder = 'videos'
            media_type = 'video'
        else:
            return jsonify({"error": "Unsupported file type"}), 400
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
        file.save(file_path)
        
        size = os.path.getsize(file_path)
        duration = request.form.get('duration', 5, type=int)
        
        conn = get_db_connection()
        conn.execute('INSERT INTO media (name, filename, type, size, duration) VALUES (?, ?, ?, ?, ?)',
                     (filename, filename, media_type, size, duration))
        conn.commit()
        conn.close()
        
        # Update media queue for players (simple implementation)
        update_media_queue()
        
        # Notify all connected players
        socketio.emit('new_media', {"filename": filename})
        
        return jsonify({"message": "File uploaded successfully", "filename": filename}), 201

def update_media_queue():
    """Update the media_queue.json file that play_server.py reads"""
    conn = get_db_connection()
    media_items = conn.execute('SELECT * FROM media').fetchall()
    conn.close()
    
    queue = []
    for item in media_items:
        folder = 'images' if item['type'] == 'image' else 'videos'
        # ALWAYS use forward slashes for the JSON path so Linux (Pi) can read it
        queue.append({
            "name": item['filename'],
            "path": f"{app.config['UPLOAD_FOLDER']}/{folder}/{item['filename']}",
            "type": item['type'],
            "duration": item['duration'],
            "played": False
        })
    
    queue_file = os.path.join(app.config['UPLOAD_FOLDER'], 'queue', 'media_queue.json')
    with open(queue_file, 'w') as f:
        json.dump(queue, f, indent=2)

@app.route('/api/devices/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    device_id = data.get('device_id')
    if not device_id:
        return jsonify({"error": "Missing device_id"}), 400
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO devices (device_id, last_seen, status)
        VALUES (?, ?, 'online')
        ON CONFLICT(device_id) DO UPDATE SET
        last_seen = excluded.last_seen,
        status = 'online'
    ''', (device_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 200

@app.route('/uploads/<folder>/<filename>')
def served_file(folder, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder), filename)

@app.route('/api/queue')
def get_queue():
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'queue'), 'media_queue.json')

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
