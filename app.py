from flask import Flask, render_template, redirect, url_for, flash, request, session, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, SubmitField, FileField, DateField, SelectField
from wtforms.validators import DataRequired, Email, Length
from models import db, User, Account, Transaction, Loan, CreditCard, Notification, FixedDeposit, RecurringDeposit, BillPayment, Insurance, Investment, Cheque, AccountStatement
from flask_migrate import Migrate
from flask_mail import Mail, Message
from twilio.rest import Client
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import random
import os
import time
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from io import BytesIO

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db.init_app(app)
migrate = Migrate(app, db)

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class TransactionForm(FlaskForm):
    account_id = IntegerField('Account ID', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])

class TransferForm(FlaskForm):
    from_account_id = IntegerField('From Account ID', validators=[DataRequired()])
    to_account_id = IntegerField('To Account ID', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])

class UploadImageForm(FlaskForm):
    image = FileField('Profile Image', validators=[DataRequired()])
    submit = SubmitField('Upload')

class LoanForm(FlaskForm):
    amount = FloatField('Loan Amount', validators=[DataRequired()])
    term_months = IntegerField('Term (Months)', validators=[DataRequired()])
    submit = SubmitField('Apply')

class CreditCardForm(FlaskForm):
    limit = FloatField('Credit Limit', validators=[DataRequired()])
    submit = SubmitField('Apply')

class ChangePasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Change Password')

class FixedDepositForm(FlaskForm):
    amount = FloatField('Deposit Amount (INR)', validators=[DataRequired()])
    term_months = IntegerField('Term (Months)', validators=[DataRequired()])
    submit = SubmitField('Create Fixed Deposit')

class RecurringDepositForm(FlaskForm):
    monthly_amount = FloatField('Monthly Amount (INR)', validators=[DataRequired()])
    term_months = IntegerField('Term (Months)', validators=[DataRequired()])
    submit = SubmitField('Create Recurring Deposit')

class BillPaymentForm(FlaskForm):
    bill_type = SelectField('Bill Type', choices=[('electricity', 'Electricity'), ('water', 'Water'), ('gas', 'Gas'), ('phone', 'Phone'), ('internet', 'Internet'), ('other', 'Other')], validators=[DataRequired()])
    bill_number = StringField('Bill Number', validators=[DataRequired()])
    amount = FloatField('Amount (INR)', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    submit = SubmitField('Pay Bill')

class InsuranceForm(FlaskForm):
    type = SelectField('Insurance Type', choices=[('life', 'Life'), ('health', 'Health'), ('vehicle', 'Vehicle')], validators=[DataRequired()])
    coverage_amount = FloatField('Coverage Amount (INR)', validators=[DataRequired()])
    term_years = IntegerField('Term (Years)', validators=[DataRequired()])
    submit = SubmitField('Apply')

class InvestmentForm(FlaskForm):
    type = SelectField('Investment Type', choices=[('mutual_fund', 'Mutual Fund'), ('stock', 'Stock'), ('bond', 'Bond')], validators=[DataRequired()])
    amount = FloatField('Investment Amount (INR)', validators=[DataRequired()])
    submit = SubmitField('Invest')

class ChequeRequestForm(FlaskForm):
    number_of_cheques = IntegerField('Number of Cheques', validators=[DataRequired()])
    submit = SubmitField('Request Cheque Book')

class AccountStatementForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Generate Statement')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter((User.email == form.email.data) | (User.username == form.username.data)).first()
        if existing_user:
            if existing_user.email == form.email.data:
                flash('Email already registered. Please use a different email.')
            else:
                flash('Username already taken. Please choose a different username.')
            return redirect(url_for('register'))
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Flush to get user.id
        # Create a default account
        account_number = str(random.randint(1000000000, 9999999999))
        account = Account(account_number=account_number, user_id=user.id)
        db.session.add(account)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    accounts = user.accounts
    current_date = datetime.now()
    yesterday = current_date - timedelta(days=1)
    two_days_ago = current_date - timedelta(days=2)
    return render_template('dashboard.html', accounts=accounts, current_user=user, current_date=current_date, yesterday=yesterday, two_days_ago=two_days_ago)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = UploadImageForm()
    if form.validate_on_submit():
        file = form.image.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{str(uuid.uuid4())}{ext}"
            upload_folder = app.config['UPLOAD_FOLDER']
            if os.path.exists(upload_folder) and not os.path.isdir(upload_folder):
                os.remove(upload_folder)
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            if os.path.exists(file_path):os.remove(file_path)
            file.save(file_path)
            user = User.query.get(session['user_id'])
            user.profile_image = unique_filename
            db.session.commit()
            flash('Profile image uploaded successfully!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF image.')
    return render_template('upload_image.html', form=form)

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = TransactionForm()
    if form.validate_on_submit():
        account = Account.query.get(form.account_id.data)
        if account and account.user_id == session['user_id']:
            account.balance += form.amount.data
            transaction = Transaction(amount=form.amount.data, transaction_type='deposit', account_id=account.id)
            db.session.add(transaction)
            db.session.commit()
            flash('Deposit successful!')
            return redirect(url_for('dashboard'))
        flash('Invalid account')
    return render_template('deposit.html', form=form, current_user=User.query.get(session['user_id']))

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = TransactionForm()
    if form.validate_on_submit():
        account = Account.query.get(form.account_id.data)
        if account and account.user_id == session['user_id'] and account.balance >= form.amount.data:
            account.balance -= form.amount.data
            transaction = Transaction(amount=form.amount.data, transaction_type='withdraw', account_id=account.id)
            db.session.add(transaction)
            db.session.commit()
            flash('Withdrawal successful!')
            return redirect(url_for('dashboard'))
        flash('Invalid account or insufficient funds')
    return render_template('withdraw.html', form=form)

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = TransferForm()
    if form.validate_on_submit():
        from_account = Account.query.get(form.from_account_id.data)
        to_account = Account.query.get(form.to_account_id.data)
        if from_account and to_account and from_account.user_id == session['user_id'] and from_account.balance >= form.amount.data:
            from_account.balance -= form.amount.data
            to_account.balance += form.amount.data
            transaction = Transaction(amount=form.amount.data, transaction_type='transfer', account_id=from_account.id, to_account_id=to_account.id)
            db.session.add(transaction)
            db.session.commit()
            flash('Transfer successful!')
            return redirect(url_for('dashboard'))
        flash('Invalid accounts or insufficient funds')
    return render_template('transfer.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    query = Transaction.query.filter(
        (Transaction.account_id.in_([account.id for account in user.accounts])) |
        (Transaction.to_account_id.in_([account.id for account in user.accounts]))
    )
    
    # Apply filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    transaction_type = request.args.get('transaction_type')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    if start_date:
        query = query.filter(Transaction.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Transaction.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if min_amount:
        query = query.filter(Transaction.amount >= float(min_amount))
    if max_amount:
        query = query.filter(Transaction.amount <= float(max_amount))
    
    user_transactions = query.order_by(Transaction.timestamp.desc()).all()
    return render_template('transactions.html', transactions=user_transactions, current_user=user)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        user.set_password(form.password.data)
        db.session.commit()
        flash('Password changed successfully!')
        return redirect(url_for('dashboard'))
    return render_template('change_password.html', form=form)

@app.route('/account_details/<int:account_id>')
def account_details(account_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    account = Account.query.get(account_id)
    if not account or account.user_id != session['user_id']:
        flash('Invalid account')
        return redirect(url_for('dashboard'))
    transactions = Transaction.query.filter(
        (Transaction.account_id == account_id) | (Transaction.to_account_id == account_id)
    ).order_by(Transaction.timestamp.desc()).all()
    return render_template('account_details.html', account=account, transactions=transactions, current_user=User.query.get(session['user_id']))

@app.route('/delete_account/<int:account_id>', methods=['POST'])
def delete_account(account_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    account = Account.query.get(account_id)
    if not account or account.user_id != session['user_id']:
        flash('Invalid account')
        return redirect(url_for('dashboard'))
    if account.balance > 0:
        flash('Cannot delete account with positive balance')
        return redirect(url_for('dashboard'))
    db.session.delete(account)
    db.session.commit()
    flash('Account deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/loans')
def loans():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_loans = Loan.query.filter_by(user_id=session['user_id']).all()
    return render_template('loans.html', loans=user_loans, current_user=User.query.get(session['user_id']))

@app.route('/apply_loan', methods=['GET', 'POST'])
def apply_loan():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = LoanForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to apply for a loan')
            return redirect(url_for('dashboard'))
        loan = Loan(amount=form.amount.data, term_months=form.term_months.data, user_id=user.id, account_id=user.accounts[0].id)
        db.session.add(loan)
        db.session.commit()
        flash('Loan application submitted!')
        return redirect(url_for('loans'))
    return render_template('apply_loan.html', form=form, current_user=User.query.get(session['user_id']))

@app.route('/credit_cards')
def credit_cards():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_cards = CreditCard.query.filter_by(user_id=session['user_id']).all()
    return render_template('credit_cards.html', cards=user_cards, current_user=User.query.get(session['user_id']))

@app.route('/apply_credit_card', methods=['GET', 'POST'])
def apply_credit_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = CreditCardForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to apply for a credit card')
            return redirect(url_for('dashboard'))
        card_number = str(random.randint(1000000000000000, 9999999999999999))
        expiry_date = f"{random.randint(1, 12):02d}/{random.randint(25, 30)}"
        cvv = str(random.randint(100, 999))
        card = CreditCard(card_number=card_number, expiry_date=expiry_date, cvv=cvv, limit=form.limit.data, user_id=user.id, account_id=user.accounts[0].id)
        db.session.add(card)
        db.session.commit()
        flash('Credit card application submitted!')
        return redirect(url_for('credit_cards'))
    return render_template('apply_credit_card.html', form=form, current_user=User.query.get(session['user_id']))

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_notifications = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=user_notifications, current_user=User.query.get(session['user_id']))

@app.route('/insurance')
def insurance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_insurance = Insurance.query.filter_by(user_id=session['user_id']).all()
    return render_template('insurance.html', insurance=user_insurance, current_user=User.query.get(session['user_id']))

@app.route('/apply_insurance', methods=['GET', 'POST'])
def apply_insurance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = InsuranceForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to apply for insurance')
            return redirect(url_for('dashboard'))
        # Calculate premium based on type and coverage
        premium_rates = {'life': 0.001, 'health': 0.002, 'vehicle': 0.003}
        premium = form.coverage_amount.data * premium_rates[form.type.data] * form.term_years.data / 12
        insurance = Insurance(type=form.type.data, coverage_amount=form.coverage_amount.data, premium_amount=premium, term_years=form.term_years.data, user_id=user.id, account_id=user.accounts[0].id)
        db.session.add(insurance)
        db.session.commit()
        flash('Insurance application submitted!')
        return redirect(url_for('insurance'))
    return render_template('apply_insurance.html', form=form)

@app.route('/investments')
def investments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_investments = Investment.query.filter_by(user_id=session['user_id']).all()
    return render_template('investments.html', investments=user_investments, current_user=User.query.get(session['user_id']))

@app.route('/apply_investment', methods=['GET', 'POST'])
def apply_investment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = InvestmentForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to invest')
            return redirect(url_for('dashboard'))
        # Simple investment logic - in real app, this would integrate with actual investment APIs
        current_value = form.amount.data * 1.05  # Assume 5% initial return
        investment = Investment(type=form.type.data, amount=form.amount.data, current_value=current_value, user_id=user.id, account_id=user.accounts[0].id)
        db.session.add(investment)
        db.session.commit()
        flash('Investment successful!')
        return redirect(url_for('investments'))
    return render_template('apply_investment.html', form=form, current_user=User.query.get(session['user_id']))

@app.route('/cheque_management')
def cheque_management():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_cheques = Cheque.query.filter_by(user_id=session['user_id']).all()
    return render_template('cheque_management.html', cheques=user_cheques, current_user=User.query.get(session['user_id']))

@app.route('/request_cheque', methods=['GET', 'POST'])
def request_cheque():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = ChequeRequestForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to request cheques')
            return redirect(url_for('dashboard'))
        # Generate cheque numbers
        for i in range(form.number_of_cheques.data):
            cheque_number = f"{user.accounts[0].account_number}_{random.randint(100000, 999999)}"
            cheque = Cheque(cheque_number=cheque_number, amount=0.0, payee='', user_id=user.id, account_id=user.accounts[0].id)
            db.session.add(cheque)
        db.session.commit()
        flash('Cheque book requested successfully!')
        return redirect(url_for('cheque_management'))
    return render_template('request_cheque.html', form=form)

def generate_statement_pdf(statement):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"SBI Account Statement")
    p.drawString(100, 730, f"Period: {statement.start_date} to {statement.end_date}")
    p.drawString(100, 710, f"Generated: {statement.created_at}")
    p.drawString(100, 690, f"Account: {statement.account.account_number}")
    p.drawString(100, 670, f"Balance: {statement.account.balance}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

@app.route('/account_statements')
def account_statements():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_statements = AccountStatement.query.filter_by(user_id=session['user_id']).all()
    return render_template('account_statements.html', statements=user_statements, current_user=User.query.get(session['user_id']))

@app.route('/download_statement/<int:statement_id>')
def download_statement(statement_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    statement = AccountStatement.query.get(statement_id)
    if not statement or statement.user_id != session['user_id']:
        flash('Invalid statement')
        return redirect(url_for('account_statements'))
    pdf_buffer = generate_statement_pdf(statement)
    return send_file(pdf_buffer, as_attachment=True, download_name=f"statement_{statement_id}.pdf", mimetype='application/pdf')

@app.route('/send_statement/<int:statement_id>', methods=['POST'])
def send_statement(statement_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    statement = AccountStatement.query.get(statement_id)
    if not statement or statement.user_id != session['user_id']:
        flash('Invalid statement')
        return redirect(url_for('account_statements'))
    send_type = request.form.get('send_type')
    contact = request.form.get('contact')
    pdf_buffer = generate_statement_pdf(statement)
    if send_type == 'email':
        msg = Message('Your SBI Account Statement', sender=app.config['MAIL_USERNAME'], recipients=[contact])
        msg.body = 'Please find your account statement attached.'
        msg.attach(f"statement_{statement_id}.pdf", 'application/pdf', pdf_buffer.getvalue())
        mail.send(msg)
        flash('Statement sent to email successfully!')
    elif send_type == 'sms':
        message = twilio_client.messages.create(
            body='Your SBI account statement has been generated. Please check your email for the PDF.',
            from_=app.config['TWILIO_PHONE_NUMBER'],
            to=contact
        )
        flash('Statement sent via SMS successfully!')
    return redirect(url_for('account_statements'))

@app.route('/generate_statement', methods=['GET', 'POST'])
def generate_statement():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = AccountStatementForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to generate statements')
            return redirect(url_for('dashboard'))
        # In a real app, generate PDF statement here
        file_path = f"statements/{user.id}_{form.start_date.data}_{form.end_date.data}.pdf"
        statement = AccountStatement(start_date=form.start_date.data, end_date=form.end_date.data, file_path=file_path, user_id=user.id, account_id=user.accounts[0].id)
        db.session.add(statement)
        db.session.commit()
        flash('Statement generated successfully!')
        return redirect(url_for('account_statements'))
    return render_template('generate_statement.html', form=form)

@app.route('/fixed_deposits')
def fixed_deposits():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_fixed_deposits = FixedDeposit.query.filter_by(user_id=session['user_id']).all()
    return render_template('fixed_deposits.html', fixed_deposits=user_fixed_deposits, current_user=User.query.get(session['user_id']))

@app.route('/apply_fixed_deposit', methods=['GET', 'POST'])
def apply_fixed_deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = FixedDepositForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to apply for fixed deposit')
            return redirect(url_for('dashboard'))
        maturity_date = datetime.now() + timedelta(days=form.term_months.data * 30)
        fixed_deposit = FixedDeposit(amount=form.amount.data, term_months=form.term_months.data, maturity_date=maturity_date, user_id=user.id, account_id=user.accounts[0].id)
        db.session.add(fixed_deposit)
        db.session.commit()
        flash('Fixed deposit application submitted!')
        return redirect(url_for('fixed_deposits'))
    return render_template('apply_fixed_deposit.html', form=form)

@app.route('/recurring_deposits')
def recurring_deposits():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_recurring_deposits = RecurringDeposit.query.filter_by(user_id=session['user_id']).all()
    return render_template('recurring_deposits.html', recurring_deposits=user_recurring_deposits, current_user=User.query.get(session['user_id']))

@app.route('/apply_recurring_deposit', methods=['GET', 'POST'])
def apply_recurring_deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = RecurringDepositForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to apply for recurring deposit')
            return redirect(url_for('dashboard'))
        maturity_date = datetime.now() + timedelta(days=form.term_months.data * 30)
        recurring_deposit = RecurringDeposit(monthly_amount=form.monthly_amount.data, term_months=form.term_months.data, maturity_date=maturity_date, user_id=user.id, account_id=user.accounts[0].id)
        db.session.add(recurring_deposit)
        db.session.commit()
        flash('Recurring deposit application submitted!')
        return redirect(url_for('recurring_deposits'))
    return render_template('apply_recurring_deposit.html', form=form)

@app.route('/bill_payments')
def bill_payments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_bills = BillPayment.query.filter_by(user_id=session['user_id']).all()
    return render_template('bill_payments.html', bills=user_bills, current_user=User.query.get(session['user_id']))

@app.route('/pay_bill', methods=['GET', 'POST'])
def pay_bill():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = BillPaymentForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if not user.accounts:
            flash('You need an account to pay bills')
            return redirect(url_for('dashboard'))
        bill = BillPayment(bill_type=form.bill_type.data, bill_number=form.bill_number.data, amount=form.amount.data, due_date=form.due_date.data, user_id=user.id, account_id=user.accounts[0].id)
        db.session.add(bill)
        db.session.commit()
        flash('Bill payment submitted!')
        return redirect(url_for('bill_payments'))
    return render_template('pay_bill.html', form=form)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Here you would typically save the contact form data to database
        # For now, we'll just flash a success message
        flash('Thank you for your message! We\'ll get back to you within 24 hours.')
        return redirect(url_for('contact'))
    return render_template('contact.html', current_user=User.query.get(session['user_id']))

@app.route('/help')
def help():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('help.html', current_user=User.query.get(session['user_id']))

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html', current_user=User.query.get(session['user_id']))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
