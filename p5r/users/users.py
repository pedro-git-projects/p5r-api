from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from p5r.db import get_db


class UsersBlueprint:
    def __init__(self, name: str, import_name: str) -> None:
        self.blueprint = Blueprint(name, import_name)
        self.setup_routes()

    def setup_routes(self):
        self.blueprint.route("/login", methods=["POST"])(self.login_user)

    def login_user(self):
        """
        Log in a user.

        ---
        tags:
          - Users
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                username:
                  type: string
                  description: The username of the user.
                password:
                  type: string
                  description: The password of the user.
        responses:
          200:
            description: Login successful.
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: A success message.
                access_token:
                  type: string
                  description: JWT access token for the user.
          401:
            description: Invalid username or password.
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
          500:
            description: Internal server error.
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
                error:
                  type: string
                  description: Detailed error information.
        """

        db = get_db()
        cursor = db.cursor()

        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return jsonify({"message": "Username and password are required"}), 400

            cursor.execute(
                "SELECT * FROM Users WHERE username = %s",
                (username,),
            )
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                access_token = create_access_token(identity=username)
                return (
                    jsonify(
                        {"message": "Login successful", "access_token": access_token}
                    ),
                    200,
                )
            else:
                return jsonify({"message": "Invalid username or password"}), 401

        except Exception as e:
            return jsonify({"message": "Error during login", "error": str(e)}), 500

        finally:
            cursor.close()
