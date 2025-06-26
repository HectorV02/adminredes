from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from models import Task
from database import db, init_db
import requests
import os

app = Flask(__name__)
ma = Marshmallow(app)
init_db(app)

# Configuración
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service:5000')

# Esquemas
class TaskSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Task

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

def validate_user_exists(user_id):
    """Valida que el usuario exista llamando al user-service"""
    try:
        response = requests.get(f'{USER_SERVICE_URL}/users/{user_id}')
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    
    # Validaciones básicas
    if not data or 'title' not in data or 'user_id' not in data:
        return jsonify({'error': 'Title and user_id are required'}), 400
    
    # Validar que el usuario exista
    if not validate_user_exists(data['user_id']):
        return jsonify({'error': 'User does not exist'}), 400
    
    # Crear la tarea
    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        user_id=data['user_id'],
        status=data.get('status', 'pendiente')
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    return task_schema.jsonify(new_task), 201

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    user_id = request.args.get('user_id')
    query = Task.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    tasks = query.all()
    return tasks_schema.jsonify(tasks), 200

@app.route('/tasks/<int:id>', methods=['GET'])
def get_task(id):
    task = Task.query.get(id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return task_schema.jsonify(task), 200

@app.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    task = Task.query.get(id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    
    # Validar estado si se proporciona
    if 'status' in data and data['status'] not in Task.STATUS_CHOICES:
        return jsonify({'error': f'Invalid status. Use: {", ".join(Task.STATUS_CHOICES)}'}), 400
    
    # Actualizar campos
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']
    if 'user_id' in data:
        if not validate_user_exists(data['user_id']):
            return jsonify({'error': 'User does not exist'}), 400
        task.user_id = data['user_id']
    
    db.session.commit()
    
    return task_schema.jsonify(task), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)