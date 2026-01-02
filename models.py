from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)  # Path to profile image
    accounts = db.relationship('Account', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)  # Balance in INR
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)  # Amount in INR
    transaction_type = db.Column(db.String(50), nullable=False)  # deposit, withdraw, transfer
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    to_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)  # for transfers

    # Define relationships
    account = db.relationship('Account', foreign_keys=[account_id], backref='transactions_from')
    to_account = db.relationship('Account', foreign_keys=[to_account_id], backref='transactions_to')

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)  # Amount in INR
    interest_rate = db.Column(db.Float, default=8.5)  # SBI loan interest rate
    term_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, paid
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class CreditCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(20), unique=True, nullable=False)
    expiry_date = db.Column(db.String(10), nullable=False)  # MM/YY
    cvv = db.Column(db.String(4), nullable=False)
    limit = db.Column(db.Float, default=50000.0)  # SBI credit limit in INR
    balance = db.Column(db.Float, default=0.0)  # Balance in INR
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class FixedDeposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)  # Amount in INR
    interest_rate = db.Column(db.Float, default=6.5)  # SBI FD interest rate
    term_months = db.Column(db.Integer, nullable=False)
    maturity_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, matured
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class RecurringDeposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monthly_amount = db.Column(db.Float, nullable=False)  # Monthly amount in INR
    interest_rate = db.Column(db.Float, default=5.5)  # SBI RD interest rate
    term_months = db.Column(db.Integer, nullable=False)
    maturity_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, matured
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class BillPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_type = db.Column(db.String(50), nullable=False)  # electricity, water, gas, phone, etc.
    bill_number = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Amount in INR
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Insurance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # life, health, vehicle
    coverage_amount = db.Column(db.Float, nullable=False)  # Coverage in INR
    premium_amount = db.Column(db.Float, nullable=False)  # Monthly premium in INR
    term_years = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, expired, claimed
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # mutual_fund, stock, bond
    amount = db.Column(db.Float, nullable=False)  # Investment amount in INR
    current_value = db.Column(db.Float, nullable=False)  # Current value in INR
    returns = db.Column(db.Float, default=0.0)  # Returns in INR
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Cheque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cheque_number = db.Column(db.String(20), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Amount in INR
    payee = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='issued')  # issued, cleared, bounced
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class AccountStatement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)  # Path to generated statement file
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())



