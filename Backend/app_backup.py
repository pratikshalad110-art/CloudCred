from flask import (
    Flask,
    request,
    jsonify,
    session,
    send_from_directory
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from werkzeug.utils import secure_filename

import os


# =========================
# FLASK APP
# =========================

app = Flask(__name__)

# Flask Session
app.secret_key = "cloudcred-secret-key"


# =========================
# BASE DIRECTORY
# =========================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================
# UPLOAD FOLDERS
# =========================

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

RESUME_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "resumes"
)

CERTIFICATE_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "certificates"
)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# =========================
# SQLITE DATABASE
# =========================

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///"
    + os.path.join(BASE_DIR, "cloudcred.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# STUDENT TABLE
# =========================

class Student(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )


# =========================
# PROFILE TABLE
# =========================

class Profile(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(20)
    )

    college = db.Column(
        db.String(150)
    )

    course = db.Column(
        db.String(100)
    )

    graduation_year = db.Column(
        db.Integer
    )


# =========================
# DOCUMENT TABLE
# =========================

class Document(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        nullable=False
    )

    filename = db.Column(
        db.String(200),
        nullable=False
    )

    file_type = db.Column(
        db.String(50),
        nullable=False
    )


# =========================
# CREATE DATABASE TABLES
# =========================

with app.app_context():

    db.create_all()

    # Create upload folders automatically
    os.makedirs(
        RESUME_FOLDER,
        exist_ok=True
    )

    os.makedirs(
        CERTIFICATE_FOLDER,
        exist_ok=True
    )


# =========================
# HOME
# =========================

@app.route("/")
def home():

    return "CloudCred Backend is Running"


# =========================
# REGISTER
# =========================

@app.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "JSON data is required"
        }), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:

        return jsonify({
            "message":
            "Name, email and password are required"
        }), 400

    existing_student = Student.query.filter_by(
        email=email
    ).first()

    if existing_student:

        return jsonify({
            "message":
            "Email already registered"
        }), 400

    hashed_password = generate_password_hash(
        password
    )

    student = Student(
        name=name,
        email=email,
        password=hashed_password
    )

    db.session.add(student)
    db.session.commit()

    return jsonify({
        "message":
        "Student registered successfully"
    }), 201


# =========================
# LOGIN
# =========================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    if not data:

        return jsonify({
            "message":
            "JSON data is required"
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:

        return jsonify({
            "message":
            "Email and password are required"
        }), 400

    student = Student.query.filter_by(
        email=email
    ).first()

    if not student:

        return jsonify({
            "message":
            "Invalid email or password"
        }), 401

    if not check_password_hash(
        student.password,
        password
    ):

        return jsonify({
            "message":
            "Invalid email or password"
        }), 401

    session["student_id"] = student.id

    return jsonify({

        "message":
        "Login successful",

        "student_id":
        student.id,

        "name":
        student.name,

        "email":
        student.email

    }), 200


# =========================
# DASHBOARD
# =========================

@app.route(
    "/dashboard",
    methods=["GET"]
)
def dashboard():

    student_id = session.get(
        "student_id"
    )

    if not student_id:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    student = db.session.get(
        Student,
        student_id
    )

    if not student:

        return jsonify({
            "message":
            "Student not found"
        }), 404

    return jsonify({

        "message":
        "Welcome to CloudCred Dashboard",

        "student_id":
        student.id,

        "name":
        student.name,

        "email":
        student.email

    }), 200


# =========================
# UPDATE PROFILE
# =========================

@app.route(
    "/profile",
    methods=["PUT"]
)
def update_profile():

    student_id = session.get(
        "student_id"
    )

    if not student_id:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    data = request.get_json()

    if not data:

        return jsonify({
            "message":
            "JSON data is required"
        }), 400

    profile = Profile.query.filter_by(
        student_id=student_id
    ).first()

    if not profile:

        profile = Profile(
            student_id=student_id
        )

        db.session.add(profile)

    profile.phone = data.get(
        "phone"
    )

    profile.college = data.get(
        "college"
    )

    profile.course = data.get(
        "course"
    )

    profile.graduation_year = data.get(
        "graduation_year"
    )

    db.session.commit()

    return jsonify({
        "message":
        "Profile updated successfully"
    }), 200


# =========================
# GET PROFILE
# =========================

@app.route(
    "/profile",
    methods=["GET"]
)
def get_profile():

    student_id = session.get(
        "student_id"
    )

    if not student_id:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    profile = Profile.query.filter_by(
        student_id=student_id
    ).first()

    if not profile:

        return jsonify({
            "message":
            "Profile not created yet"
        }), 404

    return jsonify({

        "student_id":
        profile.student_id,

        "phone":
        profile.phone,

        "college":
        profile.college,

        "course":
        profile.course,

        "graduation_year":
        profile.graduation_year

    }), 200


# =========================
# UPLOAD RESUME / CERTIFICATE
# =========================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_file():

    student_id = session.get(
        "student_id"
    )

    if not student_id:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    # Check whether file exists
    if "file" not in request.files:

        return jsonify({
            "message":
            "No file selected"
        }), 400

    file = request.files["file"]

    # Get file type
    file_type = request.form.get(
        "file_type"
    )

    # Check file type
    if file_type not in [
        "resume",
        "certificate"
    ]:

        return jsonify({
            "message":
            "file_type must be resume or certificate"
        }), 400

    # Check filename
    if file.filename == "":

        return jsonify({
            "message":
            "No file selected"
        }), 400

    # Make filename safe
    original_filename = secure_filename(
        file.filename
    )

    # Create unique filename
    filename = (
        str(student_id)
        + "_"
        + original_filename
    )

    # Select correct folder
    if file_type == "resume":

        folder = RESUME_FOLDER

    else:

        folder = CERTIFICATE_FOLDER

    # Make sure folder exists
    os.makedirs(
        folder,
        exist_ok=True
    )

    # Full file path
    file_path = os.path.join(
        folder,
        filename
    )

    # Save file locally
    file.save(
        file_path
    )

    # Save document information
    # into database
    document = Document(

        student_id=student_id,

        filename=filename,

        file_type=file_type

    )

    db.session.add(
        document
    )

    db.session.commit()

    return jsonify({

        "message":
        "File uploaded successfully",

        "filename":
        filename,

        "file_type":
        file_type

    }), 201


# =========================
# GET DOCUMENTS
# =========================

@app.route(
    "/documents",
    methods=["GET"]
)
def get_documents():

    student_id = session.get(
        "student_id"
    )

    if not student_id:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    documents = Document.query.filter_by(
        student_id=student_id
    ).all()

    result = []

    for document in documents:

        result.append({

            "id":
            document.id,

            "filename":
            document.filename,

            "file_type":
            document.file_type

        })

    return jsonify({

        "documents":
        result

    }), 200


# =========================
# DOWNLOAD DOCUMENT
# =========================

@app.route(
    "/download/<int:document_id>",
    methods=["GET"]
)
def download_document(
    document_id
):

    student_id = session.get(
        "student_id"
    )

    if not student_id:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    document = db.session.get(
        Document,
        document_id
    )

    if not document:

        return jsonify({
            "message":
            "Document not found"
        }), 404

    # Security check
    if document.student_id != student_id:

        return jsonify({
            "message":
            "Access denied"
        }), 403

    # Select folder
    if document.file_type == "resume":

        folder = RESUME_FOLDER

    else:

        folder = CERTIFICATE_FOLDER

    return send_from_directory(
        folder,
        document.filename,
        as_attachment=True
    )


# =========================
# LOGOUT
# =========================

@app.route(
    "/logout",
    methods=["POST"]
)
def logout():

    session.clear()

    return jsonify({
        "message":
        "Logout successful"
    }), 200


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )
