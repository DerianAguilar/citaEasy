from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    nit = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    cellphone = db.Column(db.String(10), unique=False, nullable=False)
    is_root = db.Column(db.Boolean, nullable=False)
    password = db.Column(db.String(100), nullable=True)
    
    companies = db.relationship('UserCompany', back_populates='user', overlaps="user, companies")
    appointments = db.relationship('Appointment', backref="user", lazy=True)

    def verify_password(self, password):
        return self.password == password

    def __repr__(self):
        return f'<User {self.name}>'

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    
    users = db.relationship('UserCompany', back_populates='company', overlaps="user, companies")
    services = db.relationship('Service', backref='company', lazy=True)
    appointments = db.relationship('Appointment', backref='company', lazy=True)

    def __repr__(self):
        return f'<Company {self.name}>'

class UserCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.identifier', ondelete="CASCADE"), nullable=False)
    company_id = db.Column(db.String(36), db.ForeignKey('company.identifier', ondelete="CASCADE"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete="SET NULL"), nullable=True)

    user = db.relationship('User', back_populates="companies", overlaps="user, companies")
    company = db.relationship('Company', back_populates="users", overlaps="user, companies")
    role = db.relationship('Role', backref=db.backref("user_company", cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<UserCompany user_id={self.user_id}, company_id={self.company_id}, role={self.role_id}>'

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(36), unique=True, nullable=False)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100))
    price = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    company_id = db.Column(db.String(36), db.ForeignKey('company.identifier', ondelete="CASCADE"), nullable=False)
    appointments = db.relationship('Appointment', backref='service', lazy=True)

    def __repr__(self):
        return f'<Service {self.title}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(36), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Time, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.identifier', ondelete="CASCADE"), nullable=False)
    company_id = db.Column(db.String(36), db.ForeignKey('company.identifier', ondelete="CASCADE"), nullable=False)
    service_id = db.Column(db.String(36), db.ForeignKey('service.identifier', ondelete="CASCADE"), nullable=False)
