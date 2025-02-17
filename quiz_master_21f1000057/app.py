from flask import Flask, render_template, redirect, url_for, flash, request, session
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
from models.models import db, User, Admin, Subject, Chapter, Quiz, Questions, Scores
from flask import render_template, request, session, redirect, url_for
from datetime import datetime, timedelta

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
@app.route('/')
def home():
    return render_template('home.html')
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
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    upcoming_quizzes = Quiz.query.order_by(Quiz.date_of_quiz.asc()).all()
    print("Upcoming Quizzes:", upcoming_quizzes)
    return render_template('user_dashboard.html', upcoming_quizzes=upcoming_quizzes)
@app.route('/admin_dashboard')
def admin_dashboard():
    subjects = Subject.query.all()
    return render_template('admin_dashboard.html', subjects=subjects)
@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out", 'info')
    return redirect(url_for('login'))


## Adding a subject in Admin Dashboard
@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if name:  # Only add subject if 'name' is provided
            # Add the new subject to the database
            new_subject = Subject(name=name, description=description)
            db.session.add(new_subject)
            db.session.commit()

            return redirect(url_for('admin_dashboard'))  # Redirect to dashboard after adding

    return render_template('add_subject.html')  # Render form page
#editting the subject name
@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)  # Fetch the subject by ID

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        # Update the subject if the name is provided
        if name:
            subject.name = name
            subject.description = description

            db.session.commit()  # Commit changes to the database
            return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard after saving

    return render_template('edit_subject.html', subject=subject)  # Pass subject data to template
#Deleting a subject
@app.route('/delete_subject/<int:subject_id>', methods=['GET'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)  # Get the subject by ID

    # Delete the subject from the database
    db.session.delete(subject)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard after deletion

#Adding a chapter in Admin Dashboard
@app.route('/add_chapter/<int:subject_id>', methods=['GET', 'POST'])
def add_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)  # Get the subject by ID
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if name:  # Only add chapter if 'name' is provided
            # Create a new chapter for the selected subject
            new_chapter = Chapter(name=name, description=description, subject_id=subject.id)
            db.session.add(new_chapter)
            db.session.commit()

            return redirect(url_for('admin_dashboard'))  # Redirect back to the dashboard after adding

    return render_template('add_chapter.html', subject=subject)  # Pass subject info to the template
# editting a chapter name
@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)  # Get the chapter by ID
    if request.method == 'POST':
        # Get the updated name and description from the form
        name = request.form.get('name')
        description = request.form.get('description')

        # Update the chapter if a new name is provided
        if name:
            chapter.name = name
            chapter.description = description  # Update description if provided
            db.session.commit()  # Commit the changes to the database

            return redirect(url_for('admin_dashboard'))  # Redirect back to the dashboard after editing

    # Render the edit chapter form
    return render_template('edit_chapter.html', chapter=chapter)
#Deleting a chapter
@app.route('/delete_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)  # Get the chapter by ID

    db.session.delete(chapter)  # Delete the chapter from the database
    db.session.commit()  # Commit the changes to the database

    return redirect(url_for('admin_dashboard'))  # Redirect back to the dashboard after deleting
#Quiz Management
@app.route('/quiz_management')
def quiz_management():
    quizzes = Quiz.query.all()  # ✅ Fetches all quizzes with their related questions
    return render_template('quiz_management.html', quizzes=quizzes)

#Adding a new quiz
from datetime import datetime  # Import this at the top

@app.route('/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if request.method == 'POST':
        chapter_id = request.form.get('chapter_id')
        date_str = request.form.get('date')  # Date is in string format
        duration = request.form.get('duration')

        if not chapter_id or not date_str or not duration:
            flash("All fields are required!", "danger")
            return redirect(url_for('add_quiz'))

        try:
            # Convert date string (dd/mm/yyyy) to a Python date object
            date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()

            new_quiz = Quiz(
                chapter_id=chapter_id,
                date_of_quiz=date_obj,  # Insert the correct date format
                time_duration=duration
            )
            db.session.add(new_quiz)
            db.session.commit()
            return redirect(url_for('quiz_management'))

        except ValueError:
            flash("Invalid date format! Use dd/mm/yyyy.", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

        return redirect(url_for('add_quiz'))

    # Fetch available chapters and subjects for dropdown
    chapters = db.session.query(Chapter.id, Chapter.name, Subject.name).join(Subject, Chapter.subject_id == Subject.id).all()
    
    return render_template('add_quiz.html', chapters=chapters)
#quiz details
@app.route('/quiz/<int:quiz_id>')
def quiz_details(quiz_id):
    quiz = db.session.query(
        Quiz.id,
        Quiz.date_of_quiz,
        Quiz.time_duration,
        Quiz.remarks,
        Chapter.name.label("chapter_name"),
        Subject.name.label("subject_name")
    ).join(Chapter, Quiz.chapter_id == Chapter.id) \
     .join(Subject, Chapter.subject_id == Subject.id) \
     .filter(Quiz.id == quiz_id) \
     .first()

    if not quiz:
        flash("Quiz not found!", "danger")
        return redirect(url_for('quiz_management'))

    return render_template('quiz_details.html', quiz=quiz)

# deleting a quiz
@app.route('/delete_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def delete_quiz(quiz_id):
    print(f"Trying to delete quiz with ID: {quiz_id}")  # Debugging
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz:
        db.session.delete(quiz)
        db.session.commit()
        print("Quiz deleted!")  # Debugging
    else:
        print("Quiz not found!")  # Debugging

    return redirect(url_for('quiz_management'))

@app.route('/add_question/<int:quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        question_title = request.form['question_title']
        question_statement = request.form['question_statement']
        option_1 = request.form['option_1']
        option_2 = request.form['option_2']
        option_3 = request.form['option_3']
        option_4 = request.form['option_4']
        correct_option = request.form['correct_option']

        new_question = Questions(
            quiz_id=quiz_id,
            question_title=question_title,
            question_statement=question_statement,
            option1=option_1,
            option2=option_2,
            option3=option_3,
            option4=option_4,
            correct_option=int(correct_option)
        )

        db.session.add(new_question)
        db.session.commit()

        return redirect(url_for('quiz_management'))  # Redirect to ensure fresh data

    questions = Questions.query.filter_by(quiz_id=quiz_id).all()
    return render_template('add_question.html', quiz=quiz, quiz_id=quiz_id, questions=questions)
#editting the question
@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Questions.query.get_or_404(question_id)

    if request.method == 'POST':
        question.question_title = request.form['question_title']
        question.question_statement = request.form['question_statement']
        question.option1 = request.form['option_1']
        question.option2 = request.form['option_2']
        question.option3 = request.form['option_3']
        question.option4 = request.form['option_4']
        question.correct_option = int(request.form['correct_option'])

        db.session.commit()
        return redirect(url_for('quiz_management'))
    return render_template('edit_question.html', question=question)
#deleting the question
@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Questions.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    return redirect(request.referrer)
## User dashboard related functions
@app.route('/quiz_info/<int:quiz_id>')
@login_required
def quiz_info(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)  # Fetch quiz or return 404 if not found
    return render_template('quiz_info.html', quiz=quiz)
from datetime import timedelta
@app.route('/start-quiz/<int:quiz_id>/<int:question_index>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id, question_index):
    # Fetch quiz and questions
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()

    if not questions:
        flash("No questions available in this quiz!", "warning")
        return redirect(url_for('user_dashboard'))

    if question_index >= len(questions):
        return redirect(url_for('quiz_results', quiz_id=quiz_id))

    current_question = questions[question_index]

    # **Reset previous selections ONLY if accessed from user dashboard**
    if request.referrer and url_for('user_dashboard') in request.referrer:
        session.pop(f'quiz_{quiz_id}_answers', None)  # Erase answers if coming from Dashboard

    # Retrieve session storage for answers (initialize if not exists)
    if f'quiz_{quiz_id}_answers' not in session:
        session[f'quiz_{quiz_id}_answers'] = {}

    user_answers = session[f'quiz_{quiz_id}_answers']

    if request.method == 'POST':
        selected_option = request.form.get('selected_option')
        action = request.form.get('action')  # Capture button action

        if selected_option:
            user_answers[str(current_question.id)] = selected_option  # Save response
            session[f'quiz_{quiz_id}_answers'] = user_answers  # Update session

        # Navigation logic
        if action == "next" and question_index + 1 < len(questions):
            return redirect(url_for('start_quiz', quiz_id=quiz_id, question_index=question_index + 1))
        elif action == "previous" and question_index > 0:
            return redirect(url_for('start_quiz', quiz_id=quiz_id, question_index=question_index - 1))
        elif action == "submit":
            return redirect(url_for('quiz_results', quiz_id=quiz_id))

    return render_template(
        'start_quiz.html',
        quiz=quiz,
        question=current_question,
        question_index=question_index,
        total_questions=len(questions),
        selected_option=user_answers.get(str(current_question.id))  # Pass saved response
    )
from datetime import datetime
def save_or_update_score(user_id, quiz_id, score):
    # Find the most recent score for this user and quiz on the same day
    existing_score = Scores.query.filter_by(user_id=user_id, quiz_id=quiz_id).filter(Scores.time_stamp_of_attempt >= datetime.utcnow().date()).first()

    if existing_score:
        # Update the existing score if the user has already attempted this quiz today
        existing_score.total_scored = score
        existing_score.time_stamp_of_attempt = datetime.utcnow()  # Update the timestamp to current time
    else:
        # If no score exists for today, create a new score record
        new_score = Scores(user_id=user_id, quiz_id=quiz_id, total_scored=score, time_stamp_of_attempt=datetime.utcnow())
        db.session.add(new_score)

    db.session.commit()  # Save changes to the database

@app.route('/quiz-results/<int:quiz_id>')
@login_required
def quiz_results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()

    # Get user answers from session
    user_answers = session.get(f'quiz_{quiz_id}_answers', {})

    results_data = []
    total_score = 0

    for question in questions:
        user_selected = user_answers.get(str(question.id))  # Get user's selected option
        correct_option = str(question.correct_option)  # Correct option as string

        # Check if the answer is correct
        is_correct = (user_selected == correct_option)
        if is_correct:
            total_score += 1  # Increment score if correct

        results_data.append({
            'question_statement': question.question_statement,
            'user_selected': user_selected,
            'correct_option': correct_option,
            'is_correct': is_correct,
            'option1': question.option1,
            'option2': question.option2,
            'option3': question.option3,
            'option4': question.option4
        })

    # Save or update the latest score using the helper function
    save_or_update_score(current_user.id, quiz_id, total_score)

    # Fetch the latest score for the given user and quiz, ordered by time
    latest_score = Scores.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).order_by(Scores.time_stamp_of_attempt.desc()).first()

    # If there is no score, default to 0
    if latest_score:
        total_score = latest_score.total_scored
    else:
        total_score = 0

    return render_template("quiz_results.html", quiz=quiz, results_data=results_data, total_score=total_score)


from sqlalchemy.sql import func
@app.route('/user-scores')
@login_required
def user_scores():
    # Get only the latest attempt per quiz
    latest_attempts = (
        db.session.query(
            Scores.quiz_id,
            func.max(Scores.time_stamp_of_attempt).label('latest_attempt')
        )
        .filter(Scores.user_id == current_user.id)  # Only the logged-in user's scores
        .group_by(Scores.quiz_id)  # Group by quiz_id to get only the latest attempt
        .all()
    )

    # Fetch quiz details and scores using the quiz_id
    quiz_scores = []
    for quiz_id, latest_attempt in latest_attempts:
        # Get the score for the latest attempt by the user for the specific quiz
        latest_score = Scores.query.filter_by(quiz_id=quiz_id, user_id=current_user.id, time_stamp_of_attempt=latest_attempt).first()

        # If the latest score is found, fetch quiz details
        if latest_score:
            quiz = Quiz.query.get(quiz_id)  # Get quiz details
            if quiz:
                quiz_scores.append({
                    "id": quiz.id,
                    "num_questions": quiz.num_questions(),  # Assuming you have this function
                    "date": latest_attempt.strftime('%d/%m/%Y'),  # Extract date only
                    "score": latest_score.total_scored  # Use the correct score
                })

    return render_template("user_scores.html", quiz_scores=quiz_scores)

from sqlalchemy import func
@app.route('/user-summary')
@login_required
def user_summary():
    # Query the number of attempts, highest score, and average score for each quiz
    quiz_summary = db.session.query(
        Scores.quiz_id,
        func.count(Scores.id).label('num_attempts'),
        func.max(Scores.total_scored).label('highest_score'),
        func.avg(Scores.total_scored).label('average_score')
    ).filter(Scores.user_id == current_user.id) \
    .group_by(Scores.quiz_id) \
    .all()

    quiz_scores = []
    for summary in quiz_summary:
        quiz = Quiz.query.get(summary.quiz_id)
        if quiz:
            # Fetch the subject name, chapter name, and total number of questions
            subject_name = quiz.get_subject_name()
            chapter_name = quiz.get_chapter_name()
            total_questions = quiz.num_questions()  # Fetch the total number of questions
            quiz_scores.append({
                'quiz_id': quiz.id,
                'subject_name': subject_name,
                'chapter_name': chapter_name,
                'total_questions': total_questions,
                'num_attempts': summary.num_attempts,
                'highest_score': round(summary.highest_score, 2),  # Round to 2 decimal places
                'average_score': round(summary.average_score, 2),  # Round to 2 decimal places
            })

    return render_template("user_summary.html", quiz_scores=quiz_scores)
     
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