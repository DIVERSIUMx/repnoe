from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import secrets
import string

# Инициализация Flask приложения
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SERVER_IP'] = '192.168.163.148'
app.config['SERVER_PORT'] = 5000

# Инициализация базы данных
db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    devices = db.relationship('Device', backref='owner', lazy=True)

# Модель устройства
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100))
    key = db.Column(db.String(8), unique=True)
    status = db.Column(db.String(20), default='offline')
    ip = db.Column(db.String(15))
    last_seen = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    commands = db.Column(db.JSON, default=list)

def generate_simple_key(length=8):
    """Генерация простого ключа устройства"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def initialize_database():
    """Инициализация базы данных"""
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin123')
            )
            db.session.add(admin_user)
            db.session.commit()

@app.route('/')
def home():
    """Главная страница с перенаправлением"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('dashboard'))
        flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('username', None)
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Панель управления устройствами"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    return render_template('dashboard.html', devices=current_user.devices)

@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    """Добавление нового устройства"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        device_key = generate_simple_key()
        new_device = Device(
            type=request.form.get('device_type'),
            description=request.form.get('description'),
            key=device_key,
            user_id=User.query.filter_by(username=session['username']).first().id
        )
        db.session.add(new_device)
        db.session.commit()
        flash(f'Устройство добавлено! Ключ: {device_key}', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_device.html')

@app.route('/device/<int:device_id>')
def device_control(device_id):
    """Страница управления устройством"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    device = Device.query.get_or_404(device_id)
    return render_template('device_control.html', device=device)

@app.route('/api/device/heartbeat', methods=['POST'])
def device_heartbeat():
    """Обновление статуса устройства (онлайн)"""
    device_key = request.args.get('key')
    if not device_key:
        return jsonify({"status": "error", "message": "Key required"}), 400
    
    device = Device.query.filter_by(key=device_key).first()
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    
    device.status = 'online'
    device.ip = request.remote_addr
    device.last_seen = datetime.now()
    db.session.commit()
    
    return jsonify({"status": "success"})

@app.route('/api/upload_photo', methods=['POST'])
def upload_photo():
    """Загрузка фото с устройства"""
    device_key = request.args.get('key')
    if not device_key:
        return jsonify({"status": "error", "message": "Key required"}), 400
    
    device = Device.query.filter_by(key=device_key).first()
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    
    if 'photo' not in request.files:
        return jsonify({"status": "error", "message": "No photo uploaded"}), 400
        
    photo_file = request.files['photo']
    if photo_file.filename == '':
        return jsonify({"status": "error", "message": "Empty filename"}), 400
    
    try:
        filename = f"device_{device.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo_file.save(save_path)
        
        device.status = 'online'
        device.last_seen = datetime.now()
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "photo_url": f"/static/uploads/{filename}"
        })
    except Exception as error:
        return jsonify({"status": "error", "message": str(error)}), 500

@app.route('/api/commands', methods=['GET'])
def get_commands():
    """Получение команд для устройства"""
    device_key = request.args.get('key')
    if not device_key:
        return jsonify({"status": "error", "message": "Key required"}), 400
    
    device = Device.query.filter_by(key=device_key).first()
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    
    commands = device.commands if device.commands else []
    device.commands = []
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "commands": commands
    })

@app.route('/api/send_command', methods=['POST'])
def send_command():
    """Отправка команды на устройство"""
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    command_data = request.get_json()
    device_id = command_data.get('device_id')
    command = command_data.get('command')
    
    device = Device.query.get(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    
    if not device.commands:
        device.commands = []
    device.commands.append(command)
    db.session.commit()
    
    return jsonify({"status": "success"})

@app.route('/api/device/status')
def device_status():
    """Проверка статуса устройств"""
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    devices = Device.query.filter(
        Device.user_id == user.id,
        Device.last_seen > datetime.now() - timedelta(minutes=5)
    ).all()
    
    return jsonify([{
        'id': device.id,
        'type': device.type,
        'status': 'online' if device.status == 'online' else 'offline',
        'last_seen': device.last_seen.isoformat() if device.last_seen else None
    } for device in devices])

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    initialize_database()
    app.run(
        host=app.config['SERVER_IP'],
        port=app.config['SERVER_PORT'],
        debug=True
    )
