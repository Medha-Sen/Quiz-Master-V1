from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'iitm_quiz_master_v1.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)
#Defining the User Table
class User(db.Model):
    #id (primary key)
    # username (email id)
    #password
    #full name
    #qualification
    #DOB
    id =db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100), unique=True, nullable=False)
    password=db.Column(db.String(100), nullable=False)
    full_name=db.Column(db.String(100), nullable=False)
    qualification=db.Column(db.String(100))
    dob=db.Column(db.Date)
    scores = db.relationship('Scores', backref='user', lazy=True)
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}')>"
class Admin(db.Model):
    #id (primary key) even though we have just one admin, we use a primary key
    #username
    #password both needed for login
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100), unique=True, nullable=False)
    password=db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Admin(id='{self.id}', username='{self.username}')>"
class Subject(db.Model):
    #id (primary key)
    # name
    # description
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100), unique=True, nullable=False)
    description=db.Column(db.Text)
    chapters=db.relationship('Chapter', backref='subject', lazy=True)
    def __repr__(self):
        return f"<Subject(id='{self.id}', name='{self.name}')>"
class Chapter(db.Model):
    #id (primary key)
    #name
    #description
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100), nullable=False)
    description=db.Column(db.Text)
    subject_id=db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    quizzes=db.relationship('Quiz', backref='chapter', lazy=True)
    def __repr__(self):
        return f"<Chapter(id='{self.id}', name='{self.name}')>"
class Quiz(db.Model):
    #id (primary key)
    #chapter_id (foreign key chapter)
    #date_of_quiz
    #time_duration(hh:mm)
    #remarks
    id=db.Column(db.Integer, primary_key=True)
    chapter_id=db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz=db.Column(db.Date)
    time_duration=db.Column(db.String(10))
    remarks=db.Column(db.Text)
    questions=db.relationship('Questions', backref='quiz', lazy=True)
    scores=db.relationship('Score', backref='quiz', lazy=True)
    def __repr__(self):
        return f"<Quiz(id='{self.id}', date_of_quiz='{self.date_of_quiz}')>"
class Questions(db.Model):
    #id (primary key)
    #quiz_id (foreign key quiz)
    #question_statement
    #option1, option2, option3, option4
    #correct option
    id=db.Column(db.Integer, primary_key=True)
    quiz_id=db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement=db.Column(db.Text,nullable=False)
    option1=db.Column(db.String(300), nullable=False)
    option2=db.Column(db.String(300), nullable=False)
    option3=db.Column(db.String(300), nullable=False)
    option4=db.Column(db.String(300), nullable=False)
    correct_option=db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return f"<Questions(id='{self.id}', question_statement='{self.question_statement}')>"
class Scores(db.Model):
    #id (primary key)
    #quiz_id (foreign key quiz)
    #user_id (foreign key user)
    #time_stamp_of_attempt
    #total_scored
    id=db.Column(db.Integer, primary_key=True)
    quiz_id=db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp_of_attempt=db.Column(db.DateTime, nullable=False)
    total_scored=db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return f"<Scores(id='{self.id}', total_scored='{self.total_scored}')>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database Created Successfully")

