import re

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user

from ..extensions import bcrypt, db
from ..models import User, UserRole

auth_bp = Blueprint("auth", __name__)


def password_error(password):
    if len(password) < 10:
        return "Password must be at least 10 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must contain a letter and a number."
    return None


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    required = ("firstName", "lastName", "email", "password")
    if any(not str(data.get(field, "")).strip() for field in required):
        return {"message": "All fields are required."}, 400

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return {"message": "An account with that email already exists."}, 409

    error = password_error(data["password"])
    if error:
        return {"message": error}, 400

    user = User(
        first_name=data["firstName"].strip(),
        last_name=data["lastName"].strip(),
        email=email,
        password_hash=bcrypt.generate_password_hash(data["password"]).decode("utf-8"),
        role=UserRole.ATTENDEE,
    )
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return {"user": user.to_dict()}, 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data.get("password", "")):
        return {"message": "Incorrect email or password."}, 401
    login_user(user, remember=bool(data.get("remember")))
    return {"user": user.to_dict()}


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    return "", 204


@auth_bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"user": None})
    return jsonify({"user": current_user.to_dict()})

