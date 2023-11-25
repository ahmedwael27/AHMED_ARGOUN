from flask import Flask, render_template, request, redirect
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
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        phone = db.Column(db.String(100))
        password = db.Column(db.String(100))
        name = db.Column(db.String(1000))
        role = db.Column(db.String(1000), default="user")


    class Teacher(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(1000))
        phone = db.Column(db.String(100), unique=True)
        password = db.Column(db.String(100))


    class Parent(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        phone = db.Column(db.String(100), unique=True)
        password = db.Column(db.String(100))
        name = db.Column(db.String(1000))


    class Student(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        grade = db.Column(db.Integer)
        parent = db.Column(db.String(100))
        name = db.Column(db.String(1000))

    class Courses(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        course_name = db.Column(db.String(1000))
        teacher_name = db.Column(db.String(100))
        teacher_phone = db.Column(db.String(100))
        grade = db.Column(db.Integer)
        rate = db.Column(db.String(100))
    db.create_all()

    class Videos(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(1000))
        description = db.Column(db.String(100))
        grade = db.Column(db.Integer)
        teacher_name = db.Column(db.String(100))
        teacher_phone = db.Column(db.String(100))
        course_name = db.Column(db.String(100))
        video_url = db.Column(db.String(200))  # New column for video URL

        def __repr__(self):
            return f"<Video {self.name}>"

    db.create_all()
class MyModelView(ModelView):
    def is_accessible(self):
            return True

admin = Admin(app)
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Teacher, db.session))
admin.add_view(MyModelView(Parent, db.session))
admin.add_view(MyModelView(Student, db.session))
admin.add_view(MyModelView(Courses, db.session))
admin.add_view(MyModelView(Videos, db.session))
@app.route("/")
def index():
    courses=Courses.query.all()
    teachers=Teacher.query.all()
    return render_template("index.html",courses=courses,teachers=teachers)

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        phone=request.form.get("phone")
        name=request.form.get("name")
        password=request.form.get("password")
        new_parent=Parent(
            phone=phone,
            password=password,
            name=name
        )
        db.session.add(new_parent)
        db.session.commit()

        new_user=User(
            phone=phone,
            password=password,
            name=name
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect("/names")
    return render_template("register_parent.html")


@app.route("/names", methods=["GET","POST"])
def names():
    if request.method == "POST":
        parent_name=request.form.get("parent_name")
        names = request.form.get("names")
        grades = request.form.get("grades")
        names_list = names.split('\n')
        grades_list = grades.split("\n")
        for i in range(len(names_list)):
            new_student = Student(
                name=names_list[i],
                grade=grades_list[i],
                parent=parent_name
            )
        return redirect("/login")
    return render_template("names.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        password = request.form.get("password")
        users = User.query.all()
        students = Student.query.all()
        for user in users:
            if phone == user.phone and password == user.password:
                users_children=[]
                for student in students:
                    if student.parent == user.name:
                        users_children.append(student.name)
                return render_template("page.html", user_phone=user.phone, users_children=users_children)

        return redirect("/register")
    return render_template("login.html")

@app.route("/page")
def page():
    all_videos=Videos.query.all()
    all_courses=Courses.query.all()
    courses=[]
    for i in all_courses:
        for v in all_videos:
            if i.course_name==v.course_name and i.teacher_phone==v.teacher_phone:
                courses.append(v)
    return render_template("page.html",all=courses,all_courses=all_courses)
@app.route("/course")
def course():
    all_courses=Courses.query.all()
    return render_template("course.html", all_courses=all_courses)

@app.route('/detail/<int:id>')
def detail(id):
    courses=Courses.query.filter_by(id=id).first()
    print (courses)
    all_videos=Videos.query.all()
    videos=[]
    if courses:
        course_name = courses.course_name
        teacher_name=courses.teacher_name
        grade = courses.grade
        for i in all_videos:
            if i.course_name==course_name and i.teacher_name==teacher_name:
                videos.append(i)

    return render_template("detail.html",videos=videos,current_name=courses.course_name)

@app.route('/video/<int:id>')
def video_detail(id):
    videos = Videos.query.filter_by(id=id)
    for video in videos:
        name=video.name
        description=video.description
        video_file=video.video_url

    return render_template("video_detail.html", videos=video, name=name,description=description,video_file=video_file)


@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/maketeacher", methods=["GET","POST"])
def maketeacher():
    if request.method == "POST":
        phone = request.form.get("phone")
        all_users=User.query.filter_by(phone=phone)
        for i in all_users:
            if phone==i.phone:
                new_teacher=Teacher(
                name=i.name,
                phone=i.phone
                )
                db.session.add(new_teacher)
                db.session.commit()
            return ('teacher')
    return render_template("maketeacher.html")


@app.route("/profile")
def profile():
     return render_template("profile.html")






if __name__=="__main__":
    app.run(debug=True)