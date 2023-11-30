from flask import Blueprint, jsonify, request
from p5r.db import get_db


class SkillsBlueprint:
    def __init__(self, name: str, import_name: str) -> None:
        self.blueprint = Blueprint(name, import_name)
        self.setup_routes()

    def setup_routes(self):
        self.blueprint.route("/skills", methods=["GET"])(self.get_all_skills)
        self.blueprint.route("/skills", methods=["POST"])(self.create_skill)

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
