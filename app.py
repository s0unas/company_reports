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
    if current_user.role != 'GM':
        flash("Access Denied.")
        return redirect(url_for('dashboard'))

    # Handle Adding New Items (Keep your existing POST logic here)
    if request.method == 'POST':
        # ... (Keep your existing 'new_email' and 'report_name' logic here) ...
        # If you deleted it, paste the logic from the previous step back in.
        # For brevity, I assume the "Add" logic is still here.
        if 'new_email' in request.form:
             # ... existing add user logic ...
             pass # Remove 'pass' when you paste your code
        elif 'report_name' in request.form:
             # ... existing add report logic ...
             pass 

    # NEW: Fetch all data to display in the table
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

# --- SETUP SCRIPT ---
# This creates the database and adds fake users/reports the first time you run it.
def initialize_db():
    with app.app_context():
        db.create_all()
        # Check if DB is empty, if so, seed data
        if not User.query.first():
            print("Creating dummy data...")
            # Create Users
            u1 = User(email='boss@company.com', password='123', role='GM')
            u2 = User(email='logistics@company.com', password='123', role='Logistics')
            u3 = User(email='sales@company.com', password='123', role='Sales')
            
            # Create Reports
            r1 = Report(name='Global Revenue 2024', link='#', group_access='Sales')
            r2 = Report(name='Shipping Manifests Dec', link='#', group_access='Logistics')
            r3 = Report(name='Confidential HR Audit', link='#', group_access='HR')
            
            db.session.add_all([u1, u2, u3, r1, r2, r3])
            db.session.commit()
            print("Database initialized.")

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True)