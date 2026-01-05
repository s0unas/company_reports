from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-for-dev' # Change this for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///company.db' # Creates local DB file
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100)) # In production, use hashed passwords!
    role = db.Column(db.String(50)) # e.g., 'GM', 'Logistics', 'Sales'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    link = db.Column(db.String(500)) # URL to the report
    group_access = db.Column(db.String(50)) # Which group can see this?

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        # Simple password check (Add hashing for real production)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
            
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # --- PERMISSION LOGIC ---
    # If GM, show everything. If not, filter by user's role.
    if current_user.role == 'GM':
        reports = Report.query.all()
    else:
        reports = Report.query.filter_by(group_access=current_user.role).all()
        
    return render_template('dashboard.html', user=current_user, reports=reports)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- ADMIN ROUTE ---
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    # 1. Security Check
    if current_user.role != 'GM':
        flash("Access Denied.")
        return redirect(url_for('dashboard'))

    # 2. Handle Form Submissions (Create User or Report)
    if request.method == 'POST':
        
        # --- CASE A: ADDING A NEW USER ---
        if 'new_email' in request.form:
            email = request.form.get('new_email')
            password = request.form.get('new_password')
            role = request.form.get('new_role')
            
            if User.query.filter_by(email=email).first():
                flash('Error: User with that email already exists.')
            else:
                new_user = User(email=email, password=password, role=role)
                db.session.add(new_user)
                db.session.commit()
                flash(f'User {email} created successfully!')

        # --- CASE B: ADDING A NEW REPORT ---
        elif 'report_name' in request.form:
            name = request.form.get('report_name')
            link = request.form.get('report_link')
            group = request.form.get('report_group')
            
            new_report = Report(name=name, link=link, group_access=group)
            db.session.add(new_report)
            db.session.commit()
            flash(f'Report "{name}" added to {group}.')

    # 3. Load Data for the Tables
    all_users = User.query.all()
    all_reports = Report.query.all()
    
    return render_template('admin.html', users=all_users, reports=all_reports)

# --- DELETE ROUTES ---
@app.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    if current_user.role == 'GM':
        user_to_delete = User.query.get(id)
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('User deleted.')
    return redirect(url_for('admin'))

@app.route('/delete_report/<int:id>')
@login_required
def delete_report(id):
    if current_user.role == 'GM':
        report_to_delete = Report.query.get(id)
        if report_to_delete:
            db.session.delete(report_to_delete)
            db.session.commit()
            flash('Report deleted.')
    return redirect(url_for('admin'))

# --- EDIT ROUTES ---
@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if current_user.role != 'GM': return redirect(url_for('dashboard'))
    
    user = User.query.get(id)
    if request.method == 'POST':
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        # Only update password if they typed something new
        new_pass = request.form.get('password')
        if new_pass:
            user.password = new_pass
            
        db.session.commit()
        flash('User updated successfully.')
        return redirect(url_for('admin'))
        
    return render_template('edit_user.html', user=user)

@app.route('/edit_report/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_report(id):
    if current_user.role != 'GM': return redirect(url_for('dashboard'))
    
    report = Report.query.get(id)
    if request.method == 'POST':
        report.name = request.form.get('name')
        report.link = request.form.get('link')
        report.group_access = request.form.get('group')
        
        db.session.commit()
        flash('Report updated successfully.')
        return redirect(url_for('admin'))
        
    return render_template('edit_report.html', report=report)

# This creates the database and the master admin if none exist
# --- SETUP SCRIPT ---
def initialize_db():
    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()
        
        # Check if there is at least one user (to ensure you aren't locked out)
        if not User.query.first():
            print("Database is empty. Creating Master Admin...")
            
            # --- THIS IS THE ONLY USER HARDCODED IN SOURCE CODE ---
            # You can change this email/password to your real one before sending
            master_admin = User(email='sohairamin@gac.com', password='soko@1999', role='GM')
            
            db.session.add(master_admin)
            db.session.commit()
            print("Master Admin created. You can now log in and create other users via the Admin Panel.")

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True)