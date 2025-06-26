from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from models import User
from database import db, init_db
import os

app = Flask(__name__)
ma = Marshmallow(app)

# Inicializa la base de datos
init_db(app)

# Esquema para serialización
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

user_schema = UserSchema()
users_schema = UserSchema(many=True)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud"""
    return jsonify({'status': 'healthy', 'message': 'Service is running'}), 200

@app.route('/users', methods=['POST'])
def create_user():
    """Crea un nuevo usuario con validaciones"""
    data = request.get_json()
    
    # Validaciones básicas
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['username', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({'error': f'Required fields: {", ".join(required_fields)}'}), 400
    
    # Validación de formato de email
    if not User.validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Verifica unicidad
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Crea el usuario
    new_user = User(username=data['username'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    
    return user_schema.jsonify(new_user), 201

@app.route('/users', methods=['GET'])
def get_all_users():
    """Obtiene todos los usuarios"""
    users = User.query.all()
    return users_schema.jsonify(users), 200

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    """Obtiene un usuario específico por ID"""
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return user_schema.jsonify(user), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)