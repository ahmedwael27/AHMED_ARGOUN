from flask import Flask, render_template, request, redirect, session,jsonify
import requests
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app=Flask(__name__)

app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
with app.app_context():
    user_course_association = db.Table(
        'user_course_association',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('course_id', db.Integer, db.ForeignKey('courses.id'))
    )


    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        phone = db.Column(db.String(100))
        password = db.Column(db.String(100))
        name = db.Column(db.String(1000))
        role = db.Column(db.String(1000), default="user")
        courses = db.relationship('Courses', secondary=user_course_association, back_populates='users')

    class Teacher(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(1000))
        phone = db.Column(db.String(100), unique=True)
        teacher_sample = db.Column(db.String(100))
        status = db.Column(db.String(100))
        videos = db.relationship('Videos', back_populates='teacher')

        def __repr__(self):
            return f"<Teacher {self.name}>"


    class Students(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_name = db.Column(db.String(1000))
        parent_phone = db.Column(db.String(100))
        parent_name = db.Column(db.String(100))
        course_name = db.Column(db.String(100))
        teacher_name = db.Column(db.String(100))
        teacher_phone = db.Column(db.String(100))


    class Courses(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        course_name = db.Column(db.String(1000))
        teacher_name = db.Column(db.String(100))
        teacher_phone = db.Column(db.String(100))
        course_price = db.Column(db.Integer)
        rate = db.Column(db.String(100))
        course_sample = db.Column(db.String(100))
        status = db.Column(db.String(100))
        users = db.relationship('User', secondary=user_course_association, back_populates='courses')

    class Videos(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(1000))
        description = db.Column(db.String(100))
        grade = db.Column(db.Integer)
        teacher_name = db.Column(db.String(100))
        teacher_phone = db.Column(db.String(100))
        course_name = db.Column(db.String(100))
        video_url = db.Column(db.String(200))  # New column for video URL
        is_checked = db.Column(db.Boolean, default=False)
        teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
        teacher = db.relationship('Teacher', back_populates='videos')

        def __repr__(self):
            return f"<Video {self.name}>"

    class Paid_courses(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        course_name = db.Column(db.String(1000))
        teacher_name = db.Column(db.String(100))
        teacher_phone = db.Column(db.String(100))
        user_name = db.Column(db.String(100))
        user_phone = db.Column(db.String(100))
        user_id = db.Column(db.String(100))
        course_id = db.Column(db.String(100))


    class Question(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        question_text = db.Column(db.String(255), nullable=False)
        course_name = db.Column(db.String(255))
        answers = db.relationship('Answer', backref='question', lazy=True)


    class Answer(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        answer_text = db.Column(db.String(255), nullable=False)
        is_correct = db.Column(db.Boolean, default=False)
        course_name = db.Column(db.String(255))
        question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)


    db.create_all()
class MyModelView(ModelView):
    def is_accessible(self):
            return True

admin = Admin(app)
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Teacher, db.session))
admin.add_view(MyModelView(Courses, db.session))
admin.add_view(MyModelView(Videos, db.session))
admin.add_view(MyModelView(Paid_courses, db.session))
admin.add_view(MyModelView(Students, db.session))
admin.add_view(MyModelView(Question, db.session))
admin.add_view(MyModelView(Answer, db.session))


# @app.route('/')
# def index():
#     questions = Question.query.all()
#     return render_template('quiz.html', questions=questions)


@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        try:
            question_text = request.form['question_text']
            answer_texts = request.form.getlist('answer_text[]')
            correct_answer_index = int(request.form['correct_answer'])

            question = Question(question_text=question_text)

            for i, answer_text in enumerate(answer_texts):
                is_correct = (i == correct_answer_index)
                answer = Answer(answer_text=answer_text, is_correct=is_correct)
                question.answers.append(answer)

            db.session.add(question)
            db.session.commit()

            return redirect('/')
        except Exception as e:
            # Handle exceptions (e.g., validation errors)
            return render_template('error.html', message=str(e))

    # Handle the GET request (if needed)
    questions = Question.query.all()
    return render_template('add_question_form.html', questions=questions)


@app.route('/quiz', methods=['GET', 'POST'])
def take_quiz():
    if request.method == 'GET':
        questions = Question.query.all()
        return render_template('quiz.html', questions=questions)
    elif request.method == 'POST':
        # Retrieve the submitted answers
        submitted_answers = request.form.to_dict()

        # Retrieve correct answers from the database
        correct_answers = Answer.query.filter_by(is_correct=True).all()

        # Calculate the score
        score = 0
        for answer in correct_answers:
            if str(answer.id) in submitted_answers and submitted_answers[str(answer.id)] == 'on':
                score += 1

        return render_template('quiz_result.html', score=score)
# @app.route("/")
# def index():
#     courses=Courses.query.all()
#     teachers=Teacher.query.all()
#     return render_template("index.html",courses=courses,teachers=teachers)

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        phone=request.form.get("phone")
        name=request.form.get("name")
        password=request.form.get("password")
        new_user=User(
            name=name,
            phone=phone,
            password=password
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")



@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        name = request.form.get("your_name")
        password = request.form.get("your_pass")
        role_user="user"
        role_teacher = "teacher"
        role_admin = "admin"

        users = User.query.all()
        for user in users:
            if name == user.name and password == user.password and role_user==user.role:
                # Assuming 'id', 'name', and 'phone' are attributes of your User model
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_phone'] = user.phone
                return redirect("/profile")

            if name == user.name and password == user.password and role_teacher==user.role:
                # Assuming 'id', 'name', and 'phone' are attributes of your User model
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_phone'] = user.phone
                return redirect("/teacher_profile")

            if name == user.name and password == user.password and role_admin==user.role:
                # Assuming 'id', 'name', and 'phone' are attributes of your User model
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_phone'] = user.phone
                return redirect("/admin_dashboard")
    return render_template("login.html")


@app.route("/profile")
def profile():
    # Retrieve user information from the session
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_phone = session.get('user_phone')
    paid_courses = Paid_courses.query.all()
    students=Students.query.all()
    all_students=[]
    my_courses = []
    for course in paid_courses:
        if user_name == course.user_name and user_phone == course.user_phone:
            my_courses.append(course)
    for student in students:
        if user_name == student.parent_name and user_phone == student.parent_phone :
            all_students.append(student)

    # Use the user information in your template
    return render_template("profile.html", user_id=user_id, user_name=user_name, user_phone=user_phone,my_courses=my_courses,all_students=all_students)

@app.route("/addchild", methods=["GET","POST"])
def addchild():
    if request.method == "POST":
        child_name = request.form.get("child_name")
        phone = request.form.get("phone")
        parent = User.query.filter_by(phone=phone).first()
        parent_name=parent.name
        new_student=Students(
            parent_name=parent_name,
            student_name=child_name,
            parent_phone=phone
        )
        db.session.add(new_student)
        db.session.commit()
        return redirect("/profile")
    return render_template("add_child.html")


@app.route("/teacher_profile")
def teacher_profile():
    # Retrieve user information from the session
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_phone = session.get('user_phone')

    # Use the user information in your template
    return render_template("teacher_profile.html", user_id=user_id, user_name=user_name, user_phone=user_phone)


@app.route("/paid_courses")
def paid():
    # Retrieve user information from the session
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_phone = session.get('user_phone')
    paid_courses=Paid_courses.query.all()
    my_courses=[]
    for course in paid_courses:
        if   user_name == course.user_name and user_phone==course.user_phone :
            my_courses.append(course)
            print (course)

    # Use the user information in your template
    return render_template("paid_courses.html", user_id=user_id, user_name=user_name, user_phone=user_phone,paid_courses=my_courses)

@app.route("/course")
def course():
    # Retrieve user information from the session
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_phone = session.get('user_phone')

    all_courses=Courses.query.filter_by(status='approved')

    # Pass user information and courses to the template
    return render_template("course.html", user_id=user_id, user_name=user_name, user_phone=user_phone, all_courses=all_courses)

@app.route('/detail/<int:id>')
def detail(id):
    course = Courses.query.filter_by(id=id).first()
    course_id=course.id
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_phone = session.get('user_phone')
    paid_courses = Paid_courses.query.all()
    all_videos = Videos.query.all()
    videos = []

    if course:
        user_name = session.get('user_name')
        course_name = course.course_name
        teacher_name = course.teacher_name
        price = course.course_price
        for c in paid_courses:
            if c.course_name == course_name and c.user_name == user_name:
                for video in all_videos:
                    if video.course_name == course_name and video.teacher_name == teacher_name :
                        videos.append(video)

    return render_template("detail.html", videos=videos, current_name=course.course_name, user_id=user_id, user_name=user_name, user_phone=user_phone, course=course)



@app.route('/video/<int:id>')
def video_detail(id):
    videos = Videos.query.filter_by(id=id)
    for video in videos:
        name=video.name
        description=video.description
        video_file=video.video_url

    return render_template("video_detail.html", videos=video, name=name,description=description,video_file=video_file)



@app.route("/buy_course/<int:id>", methods=["GET", "POST"])
def buy_course(id):
    if request.method == "GET":
        # Assuming 'id' is a parameter passed to the function
        course = Courses.query.filter_by(id=id).first()

        # Check if the course exists
        if course:
            # Extract user information from the session
            user_id = session.get('user_id')
            user_name = session.get('user_name')
            user_phone = session.get('user_phone')

            # Extract course details
            course_name = course.course_name
            teacher_name = course.teacher_name
            teacher_phone = course.teacher_phone
            course_id = course.id

            # Print the information (correct indentation)
            print(f"User ID: {user_id}")
            print(f"User Name: {user_name}")
            print(f"User Phone: {user_phone}")
            print(f"Course ID: {course_id}")
            print(f"Course Name: {course_name}")
            print(f"Teacher Name: {teacher_name}")
            print(f"Teacher Phone: {teacher_phone}")

            # Create a new record in the Paid_courses table
            buy = Paid_courses(
                course_name=course_name,
                teacher_name=teacher_name,
                teacher_phone=teacher_phone,
                course_id=id,
                user_id=user_id,
                user_name=user_name,
                user_phone=user_phone,
            )
            db.session.add(buy)
            db.session.commit()

            # Redirect to a success page or do something else
            return render_template("payment_success.html")

# @app.route("/buy_child_course/<int:id>", methods=["GET", "POST"])
# def buy_child_course(id):
#     if request.method == "POST":
#         course = Courses.query.filter_by(id=id).first()
#         student_name = request.form.get("child_name")
#
#         if course:
#             # Extract user information from the session
#             user_id = session.get('user_id')
#             parent_name = session.get('user_name')
#             parent_phone = session.get('user_phone')
#
#             course_name = course.course_name
#             teacher_name = course.teacher_name
#             teacher_phone = course.teacher_phone
#             course_id = course.id
#
#             # Validate input data
#             if not student_name:
#                 return render_template("Please provide a valid child name.")
#
#             # Check if a record with the same parent_phone already exists
#             existing_student = Student.query.filter_by(parent_phone=parent_phone).first()
#             if existing_student:
#                 return render_template("A student with the same parent phone already exists.")
#
#             # Proceed with database insertion
#             child_course = Student(
#                 course_name=course_name,
#                 teacher_name=teacher_name,
#                 teacher_phone=teacher_phone,
#                 parent_name=parent_name,
#                 parent_phone=parent_phone,
#                 student_name=student_name
#             )
#             db.session.add(child_course)
#             db.session.commit()
#
#             return redirect("/profile")  # Redirect to the profile page after buying the course
#
#     return render_template("buy_child_course.html", course_id=id)

@app.route("/admin_dashboard")
def admin_dashboard():
    # Retrieve pending teacher requests
    pending_requests = Teacher.query.filter_by(status='pending').all()
    pending_courses = Courses.query.filter_by(status='pending').all()

    return render_template("admin_dashboard.html", pending_requests=pending_requests, pending_courses=pending_courses)


@app.route("/maketeacher", methods=["GET", "POST"])
def maketeacher():
    if request.method == "POST":
        phone = request.form.get("phone")
        all_users = User.query.filter_by(phone=phone).all()
        teacher_sample= request.form.get("teacher_sample")
        for user in all_users:
            if phone == user.phone:
                new_teacher = Teacher(
                    name=user.name,
                    phone=user.phone,
                    teacher_sample= teacher_sample,
                    status='pending'

                )
                db.session.add(new_teacher)
                db.session.commit()

                return render_template("pending_accounts.html", user=user)

        return 'User not found'

    return render_template("make_teacher.html")

@app.route("/approve_teacher_request/<int:request_id>")
def approve_teacher_request(request_id):
    # Retrieve the specific teacher request
    teacher_request = Teacher.query.get(request_id)

    # Check if the teacher request exists and is 'pending'
    if teacher_request and teacher_request.status == 'pending':
        # Update the status to 'approved'
        teacher_request.status = 'approved'
        db.session.commit()

        # Update the corresponding user's role to 'teacher'
        user = User.query.filter_by(phone=teacher_request.phone).first()
        if user:
            user.role = 'teacher'
            db.session.commit()

    return redirect("/admin_dashboard")

@app.route("/view_teacher_sample/<int:request_id>")
def view_teacher_sample(request_id):
    teacher = Teacher.query.filter_by(id=request_id).first()

    if teacher:
        name = teacher.name
        phone = teacher.phone
        video_file = teacher.teacher_sample
        return render_template("view_teacher_sample.html", name=name, phone=phone, video_file=video_file)
    else:
        return "No teacher found with this ID."


@app.route("/create_course", methods=["GET","POST"])
def create_course():
    if request.method == "POST":
        course_name = request.form.get("course_name")
        teacher_name = request.form.get("teacher_name")
        teacher_phone = request.form.get("teacher_phone")
        course_price = request.form.get("course_price")
        course_sample = request.form.get("course_sample")
        new_course = Courses(
            course_name=course_name,
            teacher_name=teacher_name,
            teacher_phone=teacher_phone,
            course_price=course_price,
            course_sample=course_sample,
            status = 'pending'
        )
        db.session.add(new_course)
        db.session.commit()
        return redirect("create_video")
    return render_template("create_course.html")

@app.route("/approve_course_request/<int:course_id>")
def approve_course_request(course_id):
    # Retrieve the specific course request
    course_request = Courses.query.get(course_id)

    # Update the status to 'approved'
    if course_request:
        course_request.status = 'approved'
        db.session.commit()

    return redirect("/admin_dashboard")

@app.route("/course_detail/<int:course_id>")
def course_detail(course_id):
    # Use .first() to get the first result or None
    course = Courses.query.filter_by(id=course_id).first()

    if course:
        course_name = course.course_name
        teacher_name = course.teacher_name
        course_sample = course.course_sample

        return render_template("course_detail.html", course_name=course_name, teacher_name=teacher_name, course_sample=course_sample)
    else:
        # Handle the case where the course with the given ID is not found
        return render_template("course_not_found.html")

@app.route("/create_video", methods=["GET", "POST"])
def create_video():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        teacher_name = request.form.get("teacher_name")
        teacher_phone = request.form.get("teacher_phone")
        course_name = request.form.get("course_name")
        video_url = request.form.get("video_url")
        is_checked = request.form.get("is_checked") == "on"  # Convert checkbox value to boolean

        new_video = Videos(
            name=name,
            description=description,
            teacher_name=teacher_name,
            teacher_phone=teacher_phone,
            course_name=course_name,
            video_url=video_url,
            is_checked=is_checked,  # Add the checkbox value to the new video
        )

        db.session.add(new_video)
        db.session.commit()
        return redirect("teacher_profile")

    return render_template("create_video.html")

@app.route("/child_profile/<int:id>")
def child_profile(id):
    child = Students.query.filter_by(id=id).first()
    user_name = child.student_name
    return render_template("child_profile.html", user_name=user_name)




@app.route('/logout')
def logout():

    session.clear()
    return 'Logged out successfully'


@app.route("/contact")
def contact():
    return render_template("contact.html")



if __name__=="__main__":
    app.run(debug=True)