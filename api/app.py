import os
import time
import uuid
from flask import Flask, jsonify, request
from sqlalchemy.exc import OperationalError
from models import db, User, Company, UserCompany, Role, Service, Appointment
from datetime import datetime, timedelta

app = Flask(__name__)

HOURS_AVAILABLE_MORNING = [(8, 0), (9, 0), (10, 0), (11, 0), (12, 0)]
HOURS_AVAILABLE_AFTERNOON = [(14, 0), (15, 0), (16, 0), (17, 0)]
APPOINTMENT_DURATION = timedelta(hours=1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def wait_for_db():
    while True:
        try:
            db.engine.execute('SELECT 1')
            break
        except OperationalError:
            time.sleep(1)

def create_roles():
    roles = ['admin', 'client']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            new_role = Role(name=role_name)
            db.session.add(new_role)
    db.session.commit()

@app.before_first_request
def create_tables():
    wait_for_db()  # Esperar hasta que la base de datos esté lista
    db.create_all()  # Crear las tablas
    create_roles()  # Crear roles predefinidos

# Ruta para crear compañía con administrador
@app.route('/companies', methods=['POST'])
def create_company_with_admin():
    data = request.get_json()
    company_name = data['name']
    admin_user_identifier = data['admin_user_identifier']

    new_company = Company(name=company_name)
    db.session.add(new_company)
    db.session.commit()

    association = UserCompany(
        user_identifier=admin_user_identifier,
        company_identifier=new_company.identifier,
        role_id=Role.query.filter_by(name='admin').first().id
    )
    db.session.add(association)
    db.session.commit()

    return jsonify({"message": "Company created with admin user"}), 201

# Ruta para crear cliente para compañía
@app.route('/companies/<string:company_identifier>/clients', methods=['POST'])
def create_client_for_company(company_identifier):
    data = request.get_json()
    name = data['name']
    lastname = data['lastname']
    nit = data['nit']
    cellphone = data['cellphone']
    email = data['email']
    identifier = str(uuid.uuid4())

    new_user = User(
        identifier=identifier,
        name=name,
        lastname=lastname,
        nit=nit,
        cellphone=cellphone,
        email=email
    )
    db.session.add(new_user)
    db.session.commit()

    association = UserCompany(
        user_identifier=new_user.identifier,
        company_identifier=company_identifier,
        role_id=Role.query.filter_by(name='client').first().id
    )
    db.session.add(association)
    db.session.commit()

    return jsonify({"message": "Client created and associated with company"}), 201

# Rutas para buscar usuario y compañía por identificador
@app.route('/users/<string:user_identifier>', methods=['GET'])
def get_user_by_identifier(user_identifier):
    user = User.query.filter_by(identifier=user_identifier).first()
    if user:
        return jsonify({'id': user.id, 'username': user.username, 'email': user.email, 'identifier': user.identifier}), 200
    return jsonify({"message": "User not found"}), 404

@app.route('/companies/<string:company_identifier>', methods=['GET'])
def get_company_by_identifier(company_identifier):
    company = Company.query.filter_by(identifier=company_identifier).first()
    if company:
        return jsonify({'id': company.id, 'name': company.name, 'identifier': company.identifier}), 200
    return jsonify({"message": "Company not found"}), 404

# Ruta para crear un usuario sin relacionarlo a ninguna compañía
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data['name']
    lastname = data['lastname']
    nit = data['nit']
    cellphone = data['cellphone']
    email = data['email']
    identifier = str(uuid.uuid4())

    new_user = User(
        identifier=identifier,
        name=name,
        lastname=lastname,
        nit=nit,
        cellphone=cellphone,
        email=email
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created", "identifier": new_user.identifier}), 201

# Ruta para listar todos los usuarios
@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username, 'email': user.email, 'identifier': user.identifier} for user in users]), 200

# Ruta para listar todas las compañías
@app.route('/companies', methods=['GET'])
def list_companies():
    companies = Company.query.all()
    return jsonify([{'id': company.id, 'name': company.name, 'identifier': company.identifier} for company in companies]), 200

# Ruta para crear servicios en una compañia
@app.route('/company/<string:company_identifier>/services', methods=['POST'])
def create_service(company_identifier):
    data = request.get_json()
    title = data['title']
    description = data['description']
    price = data['price']
    identifier = str(uuid.uuid4())

    new_service = Service(
        identifier=identifier,
        title=title,
        description=description,
        price=price,
        company_id=company_identifier
    )

    db.session.add(new_service)
    db.session.commit()

    return jsonify({"message": "Service created", "identifier": new_service.identifier}), 201

@app.route('/company/<string:company_identifier>/appointment', methods=['POST'])
def create_appointment(company_identifier):
    data = request.get_json()
    date_str = data['date']
    hour_str = data['hour']
    user_id = data['user_id']
    service_id = data['service_id']
    identifier = str(uuid.uuid4())

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        hour = datetime.strptime(hour_str, '%H-%M').time()
    except ValueError:
        return jsonify({"error":"Formato de fecha incorrecto"}), 400

    new_appointment = Appointment(
        identifier=identifier,
        date=date,
        hour=hour,
        user_id=user_id,
        company_id=company_identifier,
        service_id=service_id
    )

    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({"message": "Appointment Created"}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
