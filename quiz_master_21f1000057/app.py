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
            print("Flash message triggered!")
            flash('Login Unsuccessful. Please check username and password', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)
@app.route('/user_dashboard', methods=['GET'])
@login_required
def user_dashboard():
    search_query = request.args.get('search')  
    user_id = current_user.id
    full_name = current_user.full_name  # Get the full name of the logged-in user
    current_date = datetime.now().date()

    print(f"Debug: User full name -> {full_name}")  # Debugging line

    if search_query:
        subject_filter = Subject.query.filter(Subject.name.ilike(f'%{search_query}%')).all()
        chapter_filter = Chapter.query.filter(Chapter.name.ilike(f'%{search_query}%')).all()
        quizzes = []
        for subject in subject_filter:
            for chapter in subject.chapters:
                for quiz in chapter.quizzes:
                    quizzes.append(quiz)
        for chapter in chapter_filter:
            for quiz in chapter.quizzes:
                quizzes.append(quiz)
        upcoming_quizzes = list(set(quizzes))
        if not upcoming_quizzes:
            return render_template('user_dashboard.html', user_id=user_id, full_name=full_name, upcoming_quizzes=None)

    else:
        upcoming_quizzes = Quiz.query.order_by(Quiz.date_of_quiz.asc()).all()

    return render_template('user_dashboard.html', upcoming_quizzes=upcoming_quizzes, user_id=user_id, full_name=full_name, current_date=current_date)

@app.route('/search_quizzes', methods=['GET'])
@login_required
def search_quizzes():
    search_query = request.args.get('search')
    if search_query:
        subject_filter = Subject.query.filter(Subject.name.ilike(f'%{search_query}%')).all()
        chapter_filter = Chapter.query.filter(Chapter.name.ilike(f'%{search_query}%')).all()

        quizzes = []
        for subject in subject_filter:
            for chapter in subject.chapters:
                for quiz in chapter.quizzes:
                    quizzes.append(quiz)
        for chapter in chapter_filter:
            for quiz in chapter.quizzes:
                quizzes.append(quiz)

        # Remove duplicates by converting to a set and back to a list
        upcoming_quizzes = list(set(quizzes))
        if not upcoming_quizzes:
            return render_template('user_dashboard.html', upcoming_quizzes=None)

        return render_template('user_dashboard.html', upcoming_quizzes=upcoming_quizzes)
    else:
        return redirect(url_for('user_dashboard'))  # No search query, go back to all quizzes

    return render_template('user_dashboard.html', upcoming_quizzes=upcoming_quizzes)@app.route('/admin_dashboard', methods=['GET'])
@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    search_query = request.args.get('search')

    if search_query:
        # Search for subjects matching the query
        subjects = Subject.query.filter(Subject.name.ilike(f"%{search_query}%")).all()

        # Search for chapters matching the query and get their subjects
        chapters = Chapter.query.filter(Chapter.name.ilike(f"%{search_query}%")).all()
        chapter_subjects = {chapter.subject for chapter in chapters}  # Get unique subjects from chapters

        # Combine both subject lists while avoiding duplicates
        subjects = list(set(subjects + list(chapter_subjects)))

        # If no matches found, return an empty list (404 Not Found will be displayed)
        return render_template('admin_dashboard.html', subjects=subjects)

    # Default: Show all subjects if no search query
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
@app.route('/delete_subject/<int:subject_id>', methods=['GET', 'POST'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)  # Get the subject by ID

    # Get all chapters related to this subject and delete them properly
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    for chapter in chapters:
        delete_chapter(chapter.id)  # Calls the function

    # Now delete the subject
    db.session.delete(subject)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))

# Redirect to the admin dashboard after deletion

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

    # Get all quizzes related to this chapter and delete them properly
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    for quiz in quizzes:
        delete_quiz(quiz.id)  # Calls the delete_quiz function

    # Now delete the chapter
    db.session.delete(chapter)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))
# Redirect back to the dashboard after deleting
#Quiz Management
@app.route('/quiz_management', methods=['GET', 'POST'])
def quiz_management():
    search_query = request.form.get('search_query', '')  # Get search query from the POST request
    if search_query:
        # Search by Quiz ID or Question Title
        quizzes = Quiz.query.join(Chapter).join(Subject).join(Questions).filter(
            (Quiz.id == search_query) |  # Search by Quiz ID
            (Questions.question_title.ilike(f"%{search_query}%"))  # Search by Question Title
        ).all()
        
        if not quizzes:
            return render_template('quiz_management.html', error="404 Not Found")
    else:
        # If no search query, display all quizzes
        quizzes = Quiz.query.all()

    return render_template('quiz_management.html', quizzes=quizzes, search_query=search_query)

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
#editting the quiz

from datetime import datetime

@app.route('/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)  # Fetch quiz by ID

    if request.method == 'POST':
        # Get form data and make sure field names match the HTML form
        date_str = request.form.get('date_of_quiz')
        duration = request.form.get('time_duration')
        remarks = request.form.get('remarks')

        # Debugging: Check if the form data is being passed correctly
        print(f"Form data received: date_of_quiz={date_str}, time_duration={duration}, remarks={remarks}")

        if not date_str or not duration:
            flash("Date and Duration are required!", "danger")
            return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        try:
            # Convert the date string (yyyy-mm-dd) to a Python date object
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Update the quiz fields
            quiz.date_of_quiz = date_obj
            quiz.time_duration = duration
            quiz.remarks = remarks if remarks else None

            # Commit the changes to the database
            db.session.commit()

            # Debugging: Print updated quiz details
            updated_quiz = Quiz.query.get(quiz.id)
            print(f"Updated Quiz in DB: {updated_quiz.date_of_quiz}, {updated_quiz.time_duration}, {updated_quiz.remarks}")
            # After successful update, redirect to quiz management page
            return redirect(url_for('quiz_management'))

        except ValueError:
            flash("Invalid date format! Use yyyy-mm-dd.", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            db.session.rollback()  # Rollback if there's an error

        return redirect(url_for('edit_quiz', quiz_id=quiz_id))

    # Fetch available chapters for the dropdown
    chapters = db.session.query(Chapter.id, Chapter.name).all()

    return render_template('edit_quiz.html', quiz=quiz, chapters=chapters)

# deleting a quiz
@app.route('/delete_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def delete_quiz(quiz_id):
    print(f"Trying to delete quiz with ID: {quiz_id}")  # Debugging

    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz:
        # 1️⃣ Delete all scores associated with this quiz
        Scores.query.filter_by(quiz_id=quiz_id).delete()
        print(f"Deleted all scores related to quiz {quiz_id}")

        # 2️⃣ Delete all questions related to this quiz
        Questions.query.filter_by(quiz_id=quiz_id).delete()
        print(f"Deleted all questions related to quiz {quiz_id}")

        # 3️⃣ Delete the quiz itself
        db.session.delete(quiz)
        db.session.commit()
        print(f"Quiz {quiz_id} deleted successfully!")

    else:
        print(f"Quiz {quiz_id} not found!")

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
from datetime import timedelta, datetime
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

    # Reset timer when navigating from user dashboard
    if request.referrer and url_for('user_dashboard') in request.referrer:
        session.pop(f'quiz_{quiz_id}_start_time', None)  # Reset the start time

    # Parse time_duration (stored as "hh:mm") from the database
    hours, minutes = map(int, quiz.time_duration.split(":"))  # Convert to integers

    # Initialize timer if not set
    if f'quiz_{quiz_id}_start_time' not in session:
        session[f'quiz_{quiz_id}_start_time'] = datetime.utcnow().isoformat()

    # Retrieve start time from session
    start_time = datetime.fromisoformat(session[f'quiz_{quiz_id}_start_time'])
    total_duration = timedelta(hours=hours, minutes=minutes)  # Use parsed duration
    end_time = start_time + total_duration

    # Calculate remaining time
    remaining_time = max(end_time - datetime.utcnow(), timedelta(seconds=0))
    remaining_minutes, remaining_seconds = divmod(remaining_time.seconds, 60)
    formatted_time = f"{remaining_minutes:02}:{remaining_seconds:02}"

    # Redirect to results if time is over
    if remaining_time.total_seconds() <= 0:
        flash("Time over", "danger")  # Flash the message
        return redirect(url_for('quiz_results', quiz_id=quiz_id))

    # Reset previous selections ONLY if accessed from user dashboard
    if request.referrer and url_for('user_dashboard') in request.referrer:
        session.pop(f'quiz_{quiz_id}_answers', None)

    # Retrieve session storage for answers (initialize if not exists)
    if f'quiz_{quiz_id}_answers' not in session:
        session[f'quiz_{quiz_id}_answers'] = {}

    user_answers = session[f'quiz_{quiz_id}_answers']

    if request.method == 'POST':
        selected_option = request.form.get('selected_option')
        action = request.form.get('action')

        # If no option is selected, set selected_option to None
        if not selected_option:
            selected_option = None

        if selected_option:
            user_answers[str(current_question.id)] = selected_option
            session[f'quiz_{quiz_id}_answers'] = user_answers

        # If time is up, redirect to results with "Time over" message
        if remaining_time.total_seconds() <= 0:
            flash("Time over", "danger")  # Flash the message
            return redirect(url_for('quiz_results', quiz_id=quiz_id))

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
        selected_option=user_answers.get(str(current_question.id)),
        remaining_time=formatted_time  # Pass remaining time to template
    )

from datetime import datetime
def save_or_update_score(user_id, quiz_id, score):
    # Always create a new entry for every attempt
    new_score = Scores(
        user_id=user_id,
        quiz_id=quiz_id,
        total_scored=score,
        time_stamp_of_attempt=datetime.utcnow()
    )
    db.session.add(new_score)
    db.session.commit()  # Don't forget to commit the transaction!

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
    user_id = current_user.id
    full_name = current_user.full_name  # Get the full name of the logged-in user

    # Fetch all quiz attempts for the user, ordered by quiz_id first and then by latest attempt
    all_attempts = (
        db.session.query(
            Scores.quiz_id,
            Scores.time_stamp_of_attempt,
            Scores.total_scored,
            Quiz.chapter_id
        )
        .join(Quiz, Scores.quiz_id == Quiz.id)
        .filter(Scores.user_id == user_id)  # Filter only the logged-in user's scores
        .order_by(Scores.time_stamp_of_attempt.desc()) # Ensures proper sorting
        .all()
    )

    quiz_scores = []
    for quiz_id, time_stamp, score, chapter_id in all_attempts:
        # Fetch quiz and chapter details
        quiz = Quiz.query.get(quiz_id)
        chapter = Chapter.query.get(chapter_id)

        subject_name = chapter.subject.name if chapter and chapter.subject else "Unknown Subject"
        chapter_name = chapter.name if chapter else "Unknown Chapter"

        # Get number of questions in the quiz
        num_questions = Questions.query.filter_by(quiz_id=quiz_id).count()

        quiz_scores.append({
            "id": quiz_id,
            "num_questions": num_questions,  # Correct way to fetch number of questions
            "date": time_stamp.strftime('%d/%m/%Y %H:%M'),  # Format date with time
            "score": score,
            "subject_name": subject_name,
            "chapter_name": chapter_name
        })

    return render_template("user_scores.html", user_id=user_id, full_name=full_name, quiz_scores=quiz_scores)


from sqlalchemy.orm import joinedload
from sqlalchemy import func

def get_quiz_scores(user_id):
    quiz_scores = []

    # Fetch all quizzes and their associated scores for the given user
    quizzes = db.session.query(Quiz, Scores).join(Scores, Scores.quiz_id == Quiz.id) \
        .filter(Scores.user_id == user_id) \
        .options(joinedload(Quiz.chapter).joinedload(Chapter.subject)) \
        .all()

    # Dictionary to store aggregated quiz data
    quiz_data = {}

    for quiz, score in quizzes:
        if quiz.id not in quiz_data:
            quiz_data[quiz.id] = {
                'subject_name': quiz.chapter.subject.name,
                'chapter_name': quiz.chapter.name,
                'quiz_id': quiz.id,
                'highest_score': 0,
                'total_attempts': 0,
                'total_score_sum': 0  # To calculate average
            }

        # Update highest score
        quiz_data[quiz.id]['highest_score'] = max(quiz_data[quiz.id]['highest_score'], score.total_scored)

        # Count total attempts and sum scores for average calculation
        quiz_data[quiz.id]['total_attempts'] += 1
        quiz_data[quiz.id]['total_score_sum'] += score.total_scored

    # Convert collected data into a list
    for quiz_id, data in quiz_data.items():
        data['average_score'] = round(data['total_score_sum'] / data['total_attempts'], 2) if data['total_attempts'] > 0 else 0
        quiz_scores.append(data)

    return quiz_scores

import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
import base64

import matplotlib.pyplot as plt
import io
import base64

def generate_chart_images(user_id):
    # Get the quiz scores data
    quiz_scores = get_quiz_scores(user_id)

    subject_data = {}
    for score in quiz_scores:
        subject = score['subject_name']
        highest_score = score['highest_score']
        total_attempts = score['total_attempts']

        if subject not in subject_data:
            subject_data[subject] = {"highest_score": 0, "total_attempts": 0}

        subject_data[subject]["highest_score"] = max(subject_data[subject]["highest_score"], highest_score)
        subject_data[subject]["total_attempts"] += total_attempts

    # Extract subjects, highest scores, and total attempts
    subjects = list(subject_data.keys())
    highest_scores = [subject_data[sub]["highest_score"] for sub in subjects]
    total_attempts = [subject_data[sub]["total_attempts"] for sub in subjects]

    # Plot the chart with two bars per subject
    x = range(len(subjects))
    width = 0.4  # Bar width

    plt.figure(figsize=(8, 5))
    plt.bar(x, highest_scores, width=width, label='Highest Score', color='skyblue')
    plt.bar([i + width for i in x], total_attempts, width=width, label='Total Attempts', color='orange')

    plt.xticks([i + width / 2 for i in x], subjects, rotation=30, ha='right')
    plt.ylabel('Value')
    plt.title('Highest Score and Total Attempts by Subject')
    plt.legend()

    # Save the plot as a PNG image
    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png', bbox_inches='tight')
    img_stream.seek(0)

    # Convert image to base64 for embedding in HTML
    img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')

    return img_base64


from flask import render_template
@app.route('/user_summary/<int:user_id>')
@login_required
def user_summary(user_id):
    # Fetch user details
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "danger")
        return redirect(url_for('user_dashboard'))

    quiz_scores = get_quiz_scores(user_id)
    chart_image = generate_chart_images(user_id)
    
    return render_template('user_summary.html', 
                           quiz_scores=quiz_scores, 
                           chart_image=chart_image, 
                           full_name=user.full_name)

import base64
import io
from flask import render_template, request, redirect, url_for, flash
import matplotlib.pyplot as plt


@app.route('/summary', methods=['GET', 'POST'])
def summary():
    # Search functionality
    search_query = request.form.get('user_id')
    
    if search_query:
        user = User.query.filter_by(id=search_query).first()
        
        if user:
            return redirect(url_for('user_summary', user_id=user.id))
        else:
            flash('User not found!', 'error')

    # Fetch all users and count their quiz attempts
    users = db.session.query(
        User.id,
        User.full_name,
        User.username,
        func.count(Scores.id).label('attempt_count')  # Count quiz attempts
    ).outerjoin(Scores, Scores.user_id == User.id) \
     .group_by(User.id) \
     .all()

    # Fetch quiz summary
    quizzes = db.session.query(
        Quiz.id,
        Subject.name.label('subject_name'),
        Chapter.name.label('chapter_name'),
        Quiz.date_of_quiz,
        Quiz.time_duration,
        func.count(Scores.id).label('attempt_count')  # Count attempts per quiz
    ).join(Chapter, Quiz.chapter_id == Chapter.id) \
     .join(Subject, Chapter.subject_id == Subject.id) \
     .outerjoin(Scores, Scores.quiz_id == Quiz.id) \
     .group_by(Quiz.id, Subject.name, Chapter.name, Quiz.date_of_quiz, Quiz.time_duration) \
     .all()

    # Fetch total attempts per chapter for the bar chart
    chapter_attempts = db.session.query(
        Chapter.name.label('chapter_name'),
        func.count(Scores.id).label('total_attempts')
    ).join(Quiz, Quiz.chapter_id == Chapter.id) \
     .outerjoin(Scores, Scores.quiz_id == Quiz.id) \
     .group_by(Chapter.name) \
     .all()

    # Generate the bar chart
    chart_image = generate_chart_image(chapter_attempts)

    return render_template('summary.html', users=users, quizzes=quizzes, chart_image=chart_image)
def generate_chart_image(chapter_attempts):
    # Create a Matplotlib figure
    fig, ax = plt.subplots(figsize=(10, 5))

    # Extract chapter names and number of attempts
    chapters = [record.chapter_name for record in chapter_attempts]
    attempts = [record.total_attempts for record in chapter_attempts]

    # Create a bar chart
    ax.bar(chapters, attempts, color='lightcoral')
    ax.set_xlabel('Chapter Name')
    ax.set_ylabel('Number of Attempts')
    ax.set_title('Quiz Attempts per Chapter')
    plt.xticks(rotation=45, ha='right')

    # Save the figure to a BytesIO object (in-memory image)
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)

    # Encode the image as a base64 string
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    return img_base64
### Developing API endpoints
from flask import Flask, jsonify
# Route to get all subjects
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    subjects = Subject.query.all()  # Fetch all subjects
    subjects_list = [{"id": subject.id, "name": subject.name, "description": subject.description} for subject in subjects]
    return jsonify({"subjects": subjects_list})

# Route to get all chapters for a specific subject (subject_id)
@app.route('/api/subjects/<int:subject_id>/chapters', methods=['GET'])
def get_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()  # Fetch chapters by subject_id
    chapters_list = [{"id": chapter.id, "name": chapter.name, "description": chapter.description} for chapter in chapters]
    return jsonify({"chapters": chapters_list})

# Route to get all quizzes for a specific chapter (chapter_id)
@app.route('/api/chapters/<int:chapter_id>/quizzes', methods=['GET'])
def get_quizzes(chapter_id):
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()  # Fetch quizzes by chapter_id
    quizzes_list = [
        {
            "id": quiz.id,
            "date_of_quiz": quiz.date_of_quiz,
            "time_duration": quiz.time_duration,
            "remarks": quiz.remarks,
            "subject_name": quiz.get_subject_name(),
            "chapter_name": quiz.get_chapter_name(),
            "num_questions": quiz.num_questions()
        }
        for quiz in quizzes
    ]
    return jsonify({"quizzes": quizzes_list})

# Route to get all scores for a specific user (user_id)
@app.route('/api/users/<int:user_id>/scores', methods=['GET'])
def get_scores(user_id):
    user = User.query.get(user_id)  # Fetch the user by user_id
    if not user:
        return jsonify({"error": "User not found"}), 404  # Return an error if user is not found

    scores = Scores.query.filter_by(user_id=user_id).all()  # Fetch scores by user_id
    scores_list = [
        {
            "score_id": score.id,
            "quiz_id": score.quiz_id,
            "subject_name": score.quiz.get_subject_name(),  # Fetch subject name from the quiz
            "chapter_name": score.quiz.get_chapter_name(),  # Fetch chapter name from the quiz
            "time_stamp_of_attempt": score.time_stamp_of_attempt,
            "total_score": score.total_scored
        }
        for score in scores
    ]
    
    # Return user name first followed by the scores
    return jsonify({
        "user_name": user.full_name,  # Display the user's full name first
        "scores": scores_list
    })


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