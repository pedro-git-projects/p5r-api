from flask import Blueprint, jsonify, request
from p5r.db import get_db

skills_bp = Blueprint("skills", __name__)


@skills_bp.route("/skills", methods=["GET"])
def get_all_skill():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM Skills")
    skills = cursor.fetchall()

    cursor.close()

    return jsonify(skills)


@skills_bp.route("/skills", methods=["POST"])
def create_skill():
    db = get_db()
    cursor = db.cursor()

    data = request.get_json()
    element = data.get("element")
    name = data.get("name")
    cost = data.get("cost")
    effect = data.get("effect")
    target = data.get("target")

    cursor.execute("SELECT id FROM Skills WHERE name = %s", (name,))
    existing_skill = cursor.fetchone()

    if existing_skill:
        cursor.close()
        return jsonify({"error": f"Skill with name '{name}' already exists"}), 400

    cursor.execute(
        """INSERT INTO Skills (element, name, cost, effect, target) 
        VALUES (%s, %s, %s, %s, %s)""",
        (element, name, cost, effect, target),
    )
    db.commit()

    cursor.close()

    return jsonify({"message": "Skill created successfully"}), 201


@skills_bp.route("/skills/<string:name>", methods=["GET"])
def get_skill_by_name(name):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM Skills WHERE lower(name) LIKE lower(%s)", ("%" + name + "%",)
    )
    skill = cursor.fetchone()

    cursor.close()

    if skill:
        skill_dict = {
            "id": skill[0],
            "element": skill[1],
            "name": skill[2],
            "cost": skill[3],
            "effect": skill[4],
            "target": skill[5],
        }
        return jsonify(skill_dict)
    else:
        return jsonify({"error": f"Skill with name '{name}' not found"}), 404
