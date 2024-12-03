import os
import time
import uuid
from flask import Flask, jsonify, request
from sqlalchemy.exc import OperationalError
from models import db, User, Company, UserCompany, Role, Service, Appointment
from datetime import datetime, timedelta
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import date

app = Flask(__name__)

HOURS_AVAILABLE_MORNING = [(8, 0), (9, 0), (10, 0), (11, 0), (12, 0)]
HOURS_AVAILABLE_AFTERNOON = [(14, 0), (15, 0), (16, 0), (17, 0)]
APPOINTMENT_DURATION = timedelta(hours=1)

app.config["JWT_SECRET_KEY"] = "CITA_EASY_SUPER_DUPER_SECRET"
jwt = JWTManager(app)

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

def create_super_admin():
    user_root = User.query.filter_by(is_root=True).first()

    if user_root: return

    new_user = User(
        identifier=str(uuid.uuid4()),
        name='Admin',
        lastname='Admin',
        nit='1088784321',
        cellphone='3218290361',
        email='admin@gmail.com',
        is_root=True,
        password='admin1234'
    )
    db.session.add(new_user)
    db.session.commit()

@app.before_first_request
def create_tables():
    wait_for_db()  # Esperar hasta que la base de datos esté lista
    db.create_all()  # Crear las tablas
    create_roles()  # Crear roles predefinidos
    create_super_admin() # Crear super Admin

# Crear compañía con administrador
@app.route('/companies', methods=['POST'])
@jwt_required()
def create_company_with_admin():
    claims = get_jwt()
    role_name = claims["role_name"]

    if role_name != 'root':
        return jsonify({"message": "No tienes el permiso para realizar esta acción"}), 403

    data = request.get_json()
    company_name = data['name']
    admin_user_identifier = data['admin_id']

    new_company = Company(
        identifier=str(uuid.uuid4()),
        name=company_name
        )
    db.session.add(new_company)
    db.session.commit()

    association = UserCompany(
        user_id=admin_user_identifier,
        company_id=new_company.identifier,
        role_id=Role.query.filter_by(name='admin').first().id
    )
    db.session.add(association)
    db.session.commit()

    return jsonify({"message": "Company created with admin user"}), 201

# Crear cliente para compañía
@app.route('/companies/clients/create', methods=['POST'])
@jwt_required()
def create_client_for_company():
    claims = get_jwt()
    role_name = claims["role_name"]
    company_id = claims["company_id"]

    if role_name != 'admin':
        return jsonify({"message": "No tienes el permiso para realizar esta acción"}), 403

    data = request.get_json()
    name = data['name']
    lastname = data['lastname']
    nit = data['nit']
    cellphone = data['cellphone']
    email = data['email']
    identifier = str(uuid.uuid4())

    user = User.query.filter_by(nit=nit).first()

    new_user = User(
        identifier=identifier,
        name=name,
        lastname=lastname,
        nit=nit,
        cellphone=cellphone,
        email=email,
        is_root=False
    )

    if not user:
        db.session.add(new_user)
        association = UserCompany(
            user_id=new_user.identifier,
            company_id=company_id,
            role_id=Role.query.filter_by(name='client').first().id
        )
    else:
        association = UserCompany(
            user_id=user.identifier,
            company_id=company_id,
            role_id=Role.query.filter_by(name='client').first().id
        )
    db.session.add(association)
    db.session.commit()

    return jsonify({"message": "Client created and associated with company", "identifier": new_user.identifier}), 201

# Rutas para buscar usuario y compañía por identificador
@app.route('/users/<string:nit>', methods=['GET'])
def get_user_by_identifier(nit):
    user = User.query.filter_by(nit=nit).first()
    if user:
        return jsonify({'last_name': user.lastname, 'name': user.name, 'email': user.email, 'identifier': user.identifier}), 200
    return jsonify({"message": "User not found"}), 404

@app.route('/companies/<string:company_identifier>', methods=['GET'])
def get_company_by_identifier(company_identifier):
    company = Company.query.filter_by(identifier=company_identifier).first()
    if company:
        return jsonify({'id': company.id, 'name': company.name, 'identifier': company.identifier}), 200
    return jsonify({"message": "Company not found"}), 404

# Ruta para crear un usuario sin relacionarlo a ninguna compañía
@app.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    claims = get_jwt()
    role_name = claims["role_name"]

    if role_name != 'root':
        return jsonify({"message":"No tienes permiso para realizar esta acción"}), 403

    data = request.get_json()
    name = data['name']
    lastname = data['lastname']
    nit = data['nit']
    cellphone = data['cellphone']
    email = data['email']
    password = data['password']
    identifier = str(uuid.uuid4())

    new_user = User(
        identifier=identifier,
        name=name,
        lastname=lastname,
        nit=nit,
        cellphone=cellphone,
        email=email,
        is_root=False,
        password=password
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created", "identifier": new_user.identifier}), 201

# Ruta para listar todos los usuarios
@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.name, 'email': user.email, 'identifier': user.identifier} for user in users]), 200

# Ruta para listar todas las compañías
@app.route('/companies', methods=['GET'])
def list_companies():
    companies = Company.query.all()
    return jsonify([{'id': company.id, 'name': company.name, 'identifier': company.identifier} for company in companies]), 200

@app.route('/service/<string:company_id>/services', methods=['GET'])
def list_services_of_company(company_id):
    company = Company.query.get(company_id)

    if not company:
        return jsonify({"message":"No se encontró la compañia"}), 404
    
    services = company.services

    if not services:
        return jsonify({"message":"La compañia no tiene servicios registrados"}), 200

    services_list = [
        {
            'id': service.identifier,
            'description': service.description,
            'price': service.price
        }
        for service in services
    ]
    return jsonify({"services": services_list}), 200

# Ruta para crear servicios en una compañia
@app.route('/company/services/create', methods=['POST'])
@jwt_required()
def create_service():
    claims = get_jwt()
    role_name = claims["role_name"]
    company_id = claims["company_id"]

    if role_name != 'admin':
        return jsonify({"message": "No tienes el permiso para realizar esta acción"}), 403

    data = request.get_json()
    title = data['title']
    description = data['description']
    price = data['price']
    duration = data['duration']
    identifier = str(uuid.uuid4())

    new_service = Service(
        identifier=identifier,
        title=title,
        description=description,
        price=price,
        duration=duration,
        company_id=company_id
    )

    db.session.add(new_service)
    db.session.commit()

    return jsonify({"message": "Service created", "identifier": new_service.identifier}), 201

@app.route('/company/<string:company_id>/appointment/create', methods=['POST'])
def create_appointment(company_id):
    data = request.get_json()
    date_str = data['date']
    hour_str = data['hour']
    user_id = data['user_id']
    service_id = data['service_id']
    identifier = str(uuid.uuid4())

    current_date = date.today()

    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        hour = datetime.strptime(hour_str, '%H:%M').time()
    except ValueError as e:
        return jsonify({"error": f"Formato de fecha incorrecto: {e}"}), 400

    if appointment_date <= current_date:
        return jsonify({"message": "Debes proporcionar una fecha posterior a la actual"}), 400

    new_appointment = Appointment(
        identifier=identifier,
        date=appointment_date,
        hour=hour,
        user_id=user_id,
        company_id=company_id,
        service_id=service_id
    )

    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({"message": "Appointment Created", "identifier": new_appointment.identifier}), 201

@app.route('/appointment/<string:appointment_id>/detail', methods=['GET'])
def appointment_detail(appointment_id):
    appointment = Appointment.query.filter_by(identifier=appointment_id).first()

    if not appointment:
        return jsonify({"message":"No se encontró la cita"}), 404

    service = Service.query.filter_by(identifier=appointment.service_id).first()

    hour_str = appointment.hour.strftime('%H:%M')
    date_str = appointment.date.strftime('%Y-%m-%d') 

    response = {
        "identifier": appointment.identifier,
        "service": service.title,
        "date": date_str,
        "hour": hour_str
    }

    return jsonify(response), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data["email"]
    password = data["password"]

    # Autenticar usuario
    user = User.query.filter_by(email=email).first()
    if user and user.verify_password(password):
        # Obtener todas las relaciones del usuario
        user_roles = UserCompany.query.filter_by(user_id=user.identifier).all()

        if len(user_roles) == 1:
            role_name = user_roles[0].role.name
            company_id = user_roles[0].company_id
            access_token = create_access_token(
                identity=user.identifier,
                additional_claims={
                    "role_name": role_name,
                    "company_id": company_id
                }
            )
            return jsonify(access_token=access_token), 200

        elif len(user_roles) > 1:
            options = [
                {
                    "company_id": ur.company_id,
                    "company_name": ur.company.name,
                    "role_name": ur.role.name
                }
                for ur in user_roles
            ]
            return jsonify({"message": "Select a company", "options": options}), 200
        else:
            access_token = create_access_token(
                identity=user.identifier,
                additional_claims={"role_name": 'root'}
            )
            return jsonify(access_token=access_token), 200

    return jsonify({"message": "Invalid credentials"}), 401

def select_company():
    data = request.get_json()
    company_id = data["company_id"]
    email = data["email"]

    user = User.query.filter_by(email=email).first()
    company = UserCompany.query.filter_by(company_id=company_id).first()

    acces_token = create_access_token(
        identity=user.identifier,
        additional_claims={
            "role_name": company.name,
            "company_id": company_id
        }
    )
    return jsonify(acces_token=acces_token), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
