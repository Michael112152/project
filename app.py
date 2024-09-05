import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management, replace with a secure key in production

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget_tracker.db'  # SQLite database, adjust as needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200), nullable=True)

# Routes
@app.route('/')
def index():
    """Landing page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')  # A simple welcome page

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        # Add new user to the database
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # Check password and log in user
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out the user."""
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard displaying financial overview."""
    if 'user_id' not in session:
        flash('Please log in to access your dashboard.')
        return redirect(url_for('login'))

    # Fetch user's transactions
    transactions = Transaction.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', transactions=transactions)

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    """Add a new financial transaction."""
    if 'user_id' not in session:
        flash('Please log in to add transactions.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form.get('description', '')
        date = request.form['date']

        # Create and save the new transaction
        new_transaction = Transaction(user_id=session['user_id'], amount=amount, category=category, description=description, date=date)
        db.session.add(new_transaction)
        db.session.commit()

        flash('Transaction added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add.html')

@app.route('/history')
def history():
    """Show user's transaction history."""
    if 'user_id' not in session:
        flash('Please log in to view your history.')
        return redirect(url_for('login'))

    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.date.desc()).all()
    return render_template('history.html', transactions=transactions)

@app.route('/account')
def account():
    """User account management."""
    if 'user_id' not in session:
        flash('Please log in to view your account.')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('account.html', user=user)

# Initialize the database
with app.app_context():
    db.create_all()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
