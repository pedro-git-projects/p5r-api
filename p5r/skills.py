from flask import Blueprint, jsonify, request
from p5r.db import get_db


class SkillsBlueprint:
    def __init__(self, name: str, import_name: str) -> None:
        self.blueprint = Blueprint(name, import_name)
        self.setup_routes()

    def setup_routes(self):
        self.blueprint.route("/skills", methods=["GET"])(self.get_all_skills)
        self.blueprint.route("/skills", methods=["POST"])(self.create_skill)
        self.blueprint.route("/skills/many", methods=["POST"])(self.create_skills)
        self.blueprint.route("/skills/<string:name>", methods=["GET"])(
            self.get_skill_by_name
        )

    def get_all_skills(self):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM Skills")
        skills = cursor.fetchall()

        cursor.close()

        skills_list = []
        for skill in skills:
            skill_dict = {
                "id": skill[0],
                "element": skill[1],
                "name": skill[2],
                "cost": skill[3],
                "effect": skill[4],
                "target": skill[5],
            }
            skills_list.append(skill_dict)

        return jsonify(skills_list)

    def create_skill(self):
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

    def create_skills(self):
        db = get_db()
        cursor = db.cursor()

        data = request.get_json()

        if not isinstance(data, list):
            cursor.close()
            return (
                jsonify({"error": "Invalid data format. Expected a list of skills"}),
                400,
            )

        existing_skills = []

        for skill_data in data:
            element = skill_data.get("element")
            name = skill_data.get("name")
            cost = skill_data.get("cost")
            effect = skill_data.get("effect")
            target = skill_data.get("target")

            cursor.execute("SELECT id FROM Skills WHERE name = %s", (name,))
            existing_skill = cursor.fetchone()

            if existing_skill:
                # If skill already exists, add its name to the list
                existing_skills.append(name)
            else:
                # If skill does not exist, insert it into the database
                cursor.execute(
                    """INSERT INTO Skills (element, name, cost, effect, target) 
                  VALUES (%s, %s, %s, %s, %s)""",
                    (element, name, cost, effect, target),
                )

        db.commit()

        cursor.close()

        if existing_skills:
            return (
                jsonify(
                    {"error": f"Skills with names {existing_skills} already exist"}
                ),
                400,
            )
        else:
            return jsonify({"message": "Skills created successfully"}), 201

    def get_skill_by_name(self, name: str):
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
