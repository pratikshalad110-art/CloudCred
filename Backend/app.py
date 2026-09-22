from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import os
import uuid
import qrcode


app = Flask(__name__)

# =========================================================
# FLASK SESSION
# =========================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "cloudcred-secret-key"
)

# =========================================================
# CORS
# =========================================================

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://cloudcred-1.onrender.com"
    ]
)

# =========================================================
# SESSION COOKIE
# =========================================================

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

# =========================================================
# DATABASE
# =========================================================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cloudcred.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================================================
# UPLOAD FOLDERS
# =========================================================

UPLOAD_FOLDER = "uploads"

RESUME_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "resumes"
)

CERTIFICATE_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "certificates"
)

QR_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "qr"
)

os.makedirs(
    RESUME_FOLDER,
    exist_ok=True
)

os.makedirs(
    CERTIFICATE_FOLDER,
    exist_ok=True
)

os.makedirs(
    QR_FOLDER,
    exist_ok=True
)

# =========================================================
# STUDENT TABLE
# =========================================================

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
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )


# =========================================================
# PROFILE TABLE
# =========================================================

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
        db.String(30)
    )

    college = db.Column(
        db.String(200)
    )

    course = db.Column(
        db.String(150)
    )

    graduation_year = db.Column(
        db.Integer
    )


# =========================================================
# DOCUMENT TABLE
# =========================================================

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
        db.String(255),
        nullable=False
    )

    file_type = db.Column(
        db.String(50),
        nullable=False
    )


# =========================================================
# CREDENTIAL TABLE
# =========================================================

class Credential(db.Model):

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

    credential_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    qr_filename = db.Column(
        db.String(255)
    )

    skills = db.Column(
        db.String(2000)
    )


# =========================================================
# CREATE DATABASE
# =========================================================

with app.app_context():

    db.create_all()


# =========================================================
# GET LOGGED-IN STUDENT
# =========================================================

def get_logged_in_student():

    student_id = session.get(
        "student_id"
    )

    if not student_id:
        return None

    return db.session.get(
        Student,
        student_id
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "message":
        "CloudCred Backend is Running"
    })


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "message":
            "JSON data is required"
        }), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:

        return jsonify({
            "message":
            "Name, email and password are required"
        }), 400

    email = email.strip().lower()

    existing = Student.query.filter_by(
        email=email
    ).first()

    if existing:

        return jsonify({
            "message":
            "Email already registered"
        }), 400

    student = Student(
        name=name.strip(),
        email=email,
        password=generate_password_hash(
            password
        )
    )

    db.session.add(student)

    db.session.commit()

    return jsonify({
        "message":
        "Student registered successfully",
        "student_id":
        student.id
    }), 201


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json(
        silent=True
    )

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

    email = email.strip().lower()

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

    session.clear()

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


# =========================================================
# DASHBOARD
# =========================================================

@app.route(
    "/dashboard",
    methods=["GET"]
)
def dashboard():

    student = get_logged_in_student()

    if not student:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    return jsonify({
        "message":
        "Dashboard loaded successfully",
        "student_id":
        student.id,
        "name":
        student.name,
        "email":
        student.email
    }), 200


# =========================================================
# GET PROFILE
# =========================================================

@app.route(
    "/profile",
    methods=["GET"]
)
def get_profile():

    student = get_logged_in_student()

    if not student:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    profile = Profile.query.filter_by(
        student_id=student.id
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


# =========================================================
# UPDATE PROFILE
# =========================================================

@app.route(
    "/profile",
    methods=["PUT"]
)
def update_profile():

    student = get_logged_in_student()

    if not student:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "message":
            "JSON data is required"
        }), 400

    profile = Profile.query.filter_by(
        student_id=student.id
    ).first()

    if not profile:

        profile = Profile(
            student_id=student.id
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

    graduation_year = data.get(
        "graduation_year"
    )

    if graduation_year:

        try:

            profile.graduation_year = int(
                graduation_year
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "message":
                "Graduation year must be a number"
            }), 400

    else:

        profile.graduation_year = None

    db.session.commit()

    return jsonify({
        "message":
        "Profile updated successfully"
    }), 200


# =========================================================
# UPLOAD RESUME / CERTIFICATE
# =========================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_file():

    student = get_logged_in_student()

    if not student:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    if "file" not in request.files:

        return jsonify({
            "message":
            "No file selected"
        }), 400

    file = request.files["file"]

    file_type = request.form.get(
        "file_type"
    )

    if file_type not in [
        "resume",
        "certificate"
    ]:

        return jsonify({
            "message":
            "file_type must be resume or certificate"
        }), 400

    if not file.filename:

        return jsonify({
            "message":
            "No file selected"
        }), 400

    filename = secure_filename(
        file.filename
    )

    if not filename.lower().endswith(
        ".pdf"
    ):

        return jsonify({
            "message":
            "Only PDF files are allowed"
        }), 400

    unique_filename = (
        str(student.id)
        + "_"
        + uuid.uuid4().hex[:8]
        + "_"
        + filename
    )

    if file_type == "resume":

        folder = RESUME_FOLDER

    else:

        folder = CERTIFICATE_FOLDER

    file_path = os.path.join(
        folder,
        unique_filename
    )

    file.save(file_path)

    document = Document(
        student_id=student.id,
        filename=unique_filename,
        file_type=file_type
    )

    db.session.add(document)

    db.session.commit()

    return jsonify({

        "message":
        "File uploaded successfully",

        "filename":
        unique_filename,

        "file_type":
        file_type,

        "document_id":
        document.id

    }), 201


# =========================================================
# GET DOCUMENTS
# =========================================================

@app.route(
    "/documents",
    methods=["GET"]
)
def get_documents():

    student = get_logged_in_student()

    if not student:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    documents = Document.query.filter_by(
        student_id=student.id
    ).order_by(
        Document.id.desc()
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


# =========================================================
# DOWNLOAD DOCUMENT
# =========================================================

@app.route(
    "/download/<int:document_id>",
    methods=["GET"]
)
def download_document(
    document_id
):

    student = get_logged_in_student()

    if not student:

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

    if document.student_id != student.id:

        return jsonify({
            "message":
            "Access denied"
        }), 403

    if document.file_type == "resume":

        folder = RESUME_FOLDER

    else:

        folder = CERTIFICATE_FOLDER

    return send_from_directory(
        folder,
        document.filename,
        as_attachment=True
    )


# =========================================================
# GENERATE CREDENTIAL
# =========================================================

@app.route(
    "/generate-credential",
    methods=["POST"]
)
def generate_credential():

    student = get_logged_in_student()

    if not student:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    credential = Credential.query.filter_by(
        student_id=student.id
    ).first()

    if credential:

        return jsonify({

            "message":
            "Credential already generated",

            "credential_id":
            credential.credential_id

        }), 200

    credential_id = (
        "CC-"
        + str(student.id)
        + "-"
        + uuid.uuid4().hex[:8].upper()
    )

    credential = Credential(

        student_id=
        student.id,

        credential_id=
        credential_id

    )

    db.session.add(credential)

    db.session.commit()

    return jsonify({

        "message":
        "Credential generated successfully",

        "credential_id":
        credential.credential_id

    }), 201


# =========================================================
# GENERATE QR
# =========================================================

@app.route(
    "/generate-qr",
    methods=["POST"]
)
def generate_qr():

    student = get_logged_in_student()

    if not student:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    credential = Credential.query.filter_by(
        student_id=student.id
    ).first()

    if not credential:

        return jsonify({
            "message":
            "Generate credential first"
        }), 404

    # =====================================================
    # VERIFICATION URL
    #
    # For Render:
    # Set BASE_URL in Render environment variables
    # to:
    # https://cloudcred.onrender.com
    # =====================================================

    base_url = os.environ.get(
        "BASE_URL",
        "http://127.0.0.1:5000"
    ).rstrip("/")

    verification_url = (
        base_url
        + "/verify/"
        + credential.credential_id
    )

    # =====================================================
    # QR CODE
    # =====================================================

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5
    )

    qr.add_data(
        verification_url
    )

    qr.make(
        fit=True
    )

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    qr_filename = (
        credential.credential_id
        + ".png"
    )

    qr_path = os.path.join(
        QR_FOLDER,
        qr_filename
    )

    qr_image.save(
        qr_path
    )

    credential.qr_filename = (
        qr_filename
    )

    db.session.commit()

    return jsonify({

        "message":
        "QR code generated successfully",

        "credential_id":
        credential.credential_id,

        "qr_filename":
        qr_filename,

        "verification_url":
        verification_url

    }), 201


# =========================================================
# GET QR
# =========================================================

@app.route(
    "/qr/<filename>",
    methods=["GET"]
)
def get_qr(filename):

    return send_from_directory(
        QR_FOLDER,
        filename
    )


# =========================================================
# VERIFY CREDENTIAL
# =========================================================

@app.route(
    "/verify/<credential_id>",
    methods=["GET"]
)
def verify_credential(
    credential_id
):

    credential = Credential.query.filter_by(
        credential_id=credential_id
    ).first()

    if not credential:

        return jsonify({

            "valid":
            False,

            "message":
            "INVALID credential"

        }), 404

    student = db.session.get(
        Student,
        credential.student_id
    )

    if not student:

        return jsonify({

            "valid":
            False,

            "message":
            "INVALID credential"

        }), 404

    profile = Profile.query.filter_by(
        student_id=student.id
    ).first()

    documents = Document.query.filter_by(
        student_id=student.id
    ).all()

    resume_exists = any(
        document.file_type == "resume"
        for document in documents
    )

    certificate_exists = any(
        document.file_type == "certificate"
        for document in documents
    )

    return jsonify({

        "valid":
        True,

        "message":
        "VALID credential",

        "credential_id":
        credential.credential_id,

        "student_name":
        student.name,

        "email":
        student.email,

        "college":
        profile.college
        if profile
        else None,

        "course":
        profile.course
        if profile
        else None,

        "graduation_year":
        profile.graduation_year
        if profile
        else None,

        "resume_available":
        resume_exists,

        "certificate_available":
        certificate_exists

    }), 200


# =========================================================
# AI SKILL MATCHING
# =========================================================

@app.route(
    "/skill-match",
    methods=["POST"]
)
def skill_match():

    student = get_logged_in_student()

    if not student:

        return jsonify({
            "message":
            "Please login first"
        }), 401

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "message":
            "JSON data is required"
        }), 400

    student_skills = data.get(
        "student_skills",
        []
    )

    required_skills = data.get(
        "required_skills",
        []
    )

    if not isinstance(
        student_skills,
        list
    ):

        return jsonify({
            "message":
            "student_skills must be a list"
        }), 400

    if not isinstance(
        required_skills,
        list
    ):

        return jsonify({
            "message":
            "required_skills must be a list"
        }), 400

    student_set = {

        str(skill)
        .strip()
        .lower()

        for skill in student_skills

    }

    required_set = {

        str(skill)
        .strip()
        .lower()

        for skill in required_skills

    }

    if not required_set:

        return jsonify({
            "message":
            "No required skills provided"
        }), 400

    matched_skills = (
        student_set
        & required_set
    )

    missing_skills = (
        required_set
        - student_set
    )

    score = (

        len(matched_skills)
        /
        len(required_set)

    ) * 100

    credential = Credential.query.filter_by(
        student_id=student.id
    ).first()

    if credential:

        credential.skills = ",".join(
            sorted(student_set)
        )

        db.session.commit()

    return jsonify({

        "message":
        "Skill matching completed",

        "matched_skills":
        sorted(matched_skills),

        "missing_skills":
        sorted(missing_skills),

        "match_score":
        round(score, 2)

    }), 200


# =========================================================
# LOGOUT
# =========================================================

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


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )