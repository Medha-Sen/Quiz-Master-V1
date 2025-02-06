from flask import Flask, render_template, redirect, url_for, flash, request
#database managment
from flask_sqlalchemy import SQLAlchemy
#for form handling
from flask_wtf import FlaskForm
#needed for user authentication 
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo
#needed for password hashing
from flask_bcrypt import Bcrypt
#manage user sessions
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
#importing from models.py
from models.models import db, User, Admin

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/iitm_quiz_master_v1.db'
import os

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'iitm_quiz_master_v1.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app) # connecting Flask app to SQLAlchemy database
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

#User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Admin.query.get(int(user_id))

#Form for user registration
class RegistrationForm(FlaskForm):
    username = StringField('User Name (E-mail)', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=50)])
    full_name = StringField('Full Name', validators=[DataRequired()])
    qualification = StringField('Qualification')
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])    
    submit = SubmitField('Submit')
#Form for user login
class LoginForm(FlaskForm):
    username = StringField('User Name (E-mail)', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
#Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    form=RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password, full_name=form.full_name.data, qualification=form.qualification.data, dob=form.dob.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created for '+form.username.data, 'success!!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        user = User.query.filter_by(username=form.username.data).first()
        if admin and bcrypt.check_password_hash(admin.password, form.password.data):
            login_user(admin)
            print(f"Admin Logged in as: {current_user.__class__.__name__}")  # Check the class of current_user
            return redirect(url_for('admin_dashboard'))  # Ensure it redirects to the admin dashboard
        elif user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            print(f"Logged in as: {current_user.__class__.__name__}")  # Check the class of current_user
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)
'''def login():
    form=LoginForm()
    if form.validate_on_submit():
        admin=Admin.query.filter_by(username=form.username.data).first()
        user=User.query.filter_by(username=form.username.data).first()
        if admin and bcrypt.check_password_hash(admin.password, form.password.data):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        elif user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)'''

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')
@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out", 'info')
    return redirect(url_for('login'))
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            hashed_admin_password=bcrypt.generate_password_hash('admin123pass').decode('utf-8')
            admin=Admin(username='admin1001@gmail.com', password=hashed_admin_password)
            db.session.add(admin)
            db.session.commit()
        print("Database has been intitialized with admin")
    app.run(debug=True)