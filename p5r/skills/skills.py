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
        """
        Get a list of all skills
        ---
        tags:
          - Skills
        responses:
          200:
            description: List of all skills
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: The unique identifier for the skill.
                  element:
                    type: string
                    description: The elemental affinity of the skill.
                  name:
                    type: string
                    description: The name of the skill.
                  cost:
                    type: integer
                    description: The cost associated with using the skill.
                  effect:
                    type: string
                    description: The effect of the skill.
                  target:
                    type: string
                    description: The target of the skill.
            example:
              - id: 1
                element: "pas"
                name: "Absorb Bless"
                cost: 0
                effect: "Absorbs Bless dmg"
                target: "Self"
          500:
            description: Internal Server Error. Failed to retrieve skills.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the failure to retrieve skills.
        """
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
        """
        Create a new skill
        ---
        tags:
          - Skills
        parameters:
          - in: body
            name: skill_data
            description: Data to create a new skill
            required: true
            schema:
              type: object
              properties:
                element:
                  type: string
                  description: The elemental affinity of the skill.
                name:
                  type: string
                  description: The name of the skill.
                cost:
                  type: integer
                  description: The cost associated with using the skill.
                effect:
                  type: string
                  description: The effect of the skill.
                target:
                  type: string
                  description: The target of the skill.
            example:
              element: "pas"
              name: "Absorb Bless"
              cost: 0
              effect: "Absorbs Bless dmg"
              target: "Self"
        responses:
          201:
            description: Skill created successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: A success message indicating the creation of the skill.
          400:
            description: Bad Request. Skill with the given name already exists.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating that the skill with the given name already exists.
          500:
            description: Internal Server Error. Failed to create skill.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the failure to create skill.
        """  # noqa: E501

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
        """
        Create multiple skills
        ---
        tags:
          - Skills
        parameters:
          - in: body
            name: skills_data
            description: Data to create multiple skills
            required: true
            schema:
              type: array
              items:
                type: object
                properties:
                  element:
                    type: string
                    description: The elemental affinity of the skill.
                  name:
                    type: string
                    description: The name of the skill.
                  cost:
                    type: integer
                    description: The cost associated with using the skill.
                  effect:
                    type: string
                    description: The effect of the skill.
                  target:
                    type: string
                    description: The target of the skill.
            example:
              - element: "pas"
                name: "Absorb Bless"
                cost: 0
                effect: "Absorbs Bless dmg"
                target: "Self"
              - element: "fire"
                name: "Fireball"
                cost: 10
                effect: "Deals fire damage"
                target: "Single Enemy"
        responses:
          201:
            description: Skills created successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: A success message indicating the creation of the skills.
          400:
            description: Bad Request. Some skills with the given names already exist.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating that some skills with the given names already exist.
          500:
            description: Internal Server Error. Failed to create skills.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the failure to create skills.
        """  # noqa: E501

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
        """
        Get a skill by name
        ---
        tags:
          - Skills
        parameters:
          - in: path
            name: name
            type: string
            description: The name of the skill to retrieve.
            required: true
        responses:
          200:
            description: The requested skill
            schema:
              type: object
              properties:
                id:
                  type: integer
                  description: The unique identifier for the skill.
                element:
                  type: string
                  description: The elemental affinity of the skill.
                name:
                  type: string
                  description: The name of the skill.
                cost:
                  type: integer
                  description: The cost associated with using the skill.
                effect:
                  type: string
                  description: The effect of the skill.
                target:
                  type: string
                  description: The target of the skill.
            example:
              id: 1
              element: "pas"
              name: "Absorb Bless"
              cost: 0
              effect: "Absorbs Bless dmg"
              target: "Self"
          404:
            description: Skill not found. The requested skill with the given name does not exist.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating that the skill with the given name was not found.
        """  # noqa: E501

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
