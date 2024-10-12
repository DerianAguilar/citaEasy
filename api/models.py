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
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    companies = db.relationship('Company', secondary='user_company', back_populates='users')

    def __repr__(self):
        return f'<User {self.username}>'

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    
    users = db.relationship('User', secondary='user_company', back_populates='companies')

    def __repr__(self):
        return f'<Company {self.name}>'

class UserCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.identifier'), nullable=False)
    company_id = db.Column(db.String(36), db.ForeignKey('company.identifier'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    user = db.relationship(User, backref=db.backref("user_company", cascade="all, delete-orphan"))
    company = db.relationship(Company, backref=db.backref("user_company", cascade="all, delete-orphan"))
    role = db.relationship(Role, backref=db.backref("user_company", cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<UserCompany user_id={self.user_id}, company_id={self.company_id}, role={self.role_id}>'
