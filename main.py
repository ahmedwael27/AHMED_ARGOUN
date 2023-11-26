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
        status = db.Column(db.String(100))
        videos = db.relationship('Videos', back_populates='teacher')

        def __repr__(self):
            return f"<Teacher {self.name}>"


    class Courses(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        course_name = db.Column(db.String(1000))
        teacher_name = db.Column(db.String(100))
        teacher_phone = db.Column(db.String(100))
        grade = db.Column(db.Integer)
        rate = db.Column(db.String(100))

    class Videos(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(1000))
        description = db.Column(db.String(100))
        grade = db.Column(db.Integer)
        teacher_name = db.Column(db.String(100))
        teacher_phone = db.Column(db.String(100))
        course_name = db.Column(db.String(100))
        video_url = db.Column(db.String(200))  # New column for video URL
        teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
        teacher = db.relationship('Teacher', back_populates='videos')

        def __repr__(self):
            return f"<Video {self.name}>"



    db.create_all()
class MyModelView(ModelView):
    def is_accessible(self):
            return True

admin = Admin(app)
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Teacher, db.session))
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
        name = request.form.get("name")
        phone = request.form.get("phone")
        password = request.form.get("password")
        users = User.query.all()
        for user in users:
            if name == user.name and password == user.password :
                return redirect("/profile")
    return render_template("login.html")

@app.route("/profile")
def profile():
    all_videos=Videos.query.all()
    all_courses=Courses.query.all()
    courses=[]
    for i in all_courses:
        for v in all_videos:
            if i.course_name==v.course_name and i.teacher_phone==v.teacher_phone:
                courses.append(v)
    return render_template("profile.html",all=courses,all_courses=all_courses)
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

@app.route("/maketeacher", methods=["GET", "POST"])
def maketeacher():
    if request.method == "POST":
        phone = request.form.get("phone")
        all_users = User.query.filter_by(phone=phone).all()

        for user in all_users:
            if phone == user.phone:
                new_teacher = Teacher(
                    name=user.name,
                    phone=user.phone,
                    status='pending'  # 'pending' status indicates awaiting admin approval
                )
                db.session.add(new_teacher)
                db.session.commit()

                return redirect("/admin_dashboard")

        return 'User not found'

    return render_template("maketeacher.html")


def get_pending_teacher_requests():
    return Teacher.query.filter_by(status='pending').all()

@app.route("/admin_dashboard")
def admin_dashboard():
    # Retrieve pending teacher requests
    pending_requests = get_pending_teacher_requests()
    return render_template("admin_dashboard.html", pending_requests=pending_requests)

@app.route("/approve_teacher_request/<int:request_id>")
def approve_teacher_request(request_id):
    # Retrieve the specific teacher request
    teacher_request = Teacher.query.get(request_id)

    # Update the status to 'approved' and change the user to a teacher
    if teacher_request:
        teacher_request.status = 'approved'
        db.session.commit()

    return redirect("/admin_dashboard")



@app.route("/view_teacher/<int:teacher_id>")
def view_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    return render_template("view_teacher.html", teacher=teacher)

@app.route("/play_video_sample/<int:teacher_id>")
def play_video_sample(teacher_id):
    # Assuming you have a VideoSample model with appropriate fields
    videos = Videos.query.filter_by(teacher_id=teacher_id).all()
    if videos:
        return render_template("play_video_sample.html", videos=videos)
    else:
        return "No videos found for this teacher."










if __name__=="__main__":
    app.run(debug=True)