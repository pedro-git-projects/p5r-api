from typing import Any, Dict, List
from flask import Blueprint, jsonify, request
from p5r.db import get_db


class PersonaBlueprint:
    def __init__(self, name: str, import_name: str) -> None:
        self.blueprint = Blueprint(name, import_name)
        self.setup_routes()

    def setup_routes(self):
        self.blueprint.route("/personas", methods=["GET"])(self.get_all_personas)
        self.blueprint.route("/personas", methods=["POST"])(self.create_persona)
        self.blueprint.route("/personas/many", methods=["POST"])(self.create_personas)
        self.blueprint.route("/personas/<string:name>", methods=["GET"])(
            self.get_persona_by_name
        )
        self.blueprint.route("/personas/detailed/<string:name>", methods=["GET"])(
            self.get_detailed_persona_by_name
        )

        self.blueprint.route("/personas/<string:name>", methods=["DELETE"])(
            self.delete_persona_by_name
        )
        self.blueprint.route("/personas/<string:name>", methods=["PUT"])(
            self.update_persona_by_name
        )

    def get_all_personas(self):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM Personas")
        personas = cursor.fetchall()

        personas_list = []
        for persona in personas:
            persona_dict = {
                "id": persona[0],
                "name": persona[1],
                "inherits": persona[2],
                "item": persona[3],
                "itemr": persona[4],
                "lvl": persona[5],
                "trait": persona[6],
                "arcana": persona[7],
                "resists": self.__get_resists_for_persona(cursor, persona[0]),
                "skills": self.__get_skills_for_persona(cursor, persona[0]),
                "stats": self.__get_stats_for_persona(cursor, persona[0]),
            }
            personas_list.append(persona_dict)

        cursor.close()

        return jsonify(personas_list)

    def get_persona_by_name(self, name: str):
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM Personas WHERE lower(name) LIKE lower(%s)",
            ("%" + name + "%",),
        )
        persona = cursor.fetchone()

        if not persona:
            return jsonify({"error": "Persona not found"}), 404

        persona_dict = {
            "id": persona[0],
            "name": persona[1],
            "inherits": persona[2],
            "item": persona[3],
            "itemr": persona[4],
            "lvl": persona[5],
            "trait": persona[6],
            "arcana": persona[7],
            "resists": self.__get_resists_for_persona(cursor, persona[0]),
            "skills": self.__get_skills_for_persona(cursor, persona[0]),
            "stats": self.__get_stats_for_persona(cursor, persona[0]),
        }

        cursor.close()

        return jsonify(persona_dict)

    def get_detailed_persona_by_name(self, name: str):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM Personas WHERE lower(name) = lower(%s)", (name,))
        persona = cursor.fetchone()

        if not persona:
            cursor.close()
            return jsonify({"error": "Persona not found"}), 404

        persona_dict = {
            "id": persona[0],
            "name": persona[1],
            "inherits": persona[2],
            "item": persona[3],
            "itemr": persona[4],
            "lvl": persona[5],
            "trait": persona[6],
            "arcana": persona[7],
            "resists": self.__get_resists_for_persona(cursor, persona[0]),
            "skills": self.__get_skills_for_persona(cursor, persona[0]),
            "detailed_skills": self.__get_skills_for_persona_by_name(cursor, name),
            "stats": self.__get_stats_for_persona(cursor, persona[0]),
        }

        cursor.close()

        return jsonify(persona_dict)

    def create_persona(self):
        db = get_db()
        cursor = db.cursor()

        try:
            data = request.get_json()
            name = data["name"]
            cursor.execute(
                "SELECT id FROM Personas WHERE lower(name) = lower(%s)", (name,)
            )
            existing_persona = cursor.fetchone()

            if existing_persona:
                return (
                    jsonify(
                        {"error": f"A persona with the name '{name}' already exists"}
                    ),
                    400,
                )

            inherits = data["inherits"]
            item = data["item"]
            itemr = data["itemr"]
            lvl = data["lvl"]
            trait = data["trait"]
            arcana = data["arcana"]

            cursor.execute(
                """INSERT INTO Personas 
                  (name, inherits, item, itemr, lvl, trait, arcana) 
                  VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (name, inherits, item, itemr, lvl, trait, arcana),
            )

            persona_id = 0
            row = cursor.fetchone()

            if row is None:
                return (
                    jsonify({"error": "An error occurred on our side"}),
                    500,
                )
            else:
                persona_id = row[0]

            resistances = data.get("resists", {})
            cursor.execute(
                """INSERT INTO PersonaResistances 
              (persona_id, phys, gun, fire, ice, elec, wind, pys, nuke, bless, curse) 
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    persona_id,
                    resistances.get("phys", ""),
                    resistances.get("gun", ""),
                    resistances.get("fire", ""),
                    resistances.get("ice", ""),
                    resistances.get("elec", ""),
                    resistances.get("wind", ""),
                    resistances.get("pys", ""),
                    resistances.get("nuke", ""),
                    resistances.get("bless", ""),
                    resistances.get("curse", ""),
                ),
            )

            skills = data.get("skills", {})
            for skill_name, level in skills.items():
                cursor.execute(
                    """INSERT INTO PersonaSkills (persona_id, name, level) 
                  VALUES (%s, %s, %s)""",
                    (persona_id, skill_name, level),
                )

            stats = data.get("stats", {})
            cursor.execute(
                """INSERT INTO PersonaStats (persona_id, st, ma, en, ag, lu) 
              VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    persona_id,
                    stats.get("st", 0),
                    stats.get("ma", 0),
                    stats.get("en", 0),
                    stats.get("ag", 0),
                    stats.get("lu", 0),
                ),
            )

            db.commit()
            cursor.close()

            return jsonify({"id": persona_id}), 201
        except Exception as e:
            print(f"Error creating Persona: {str(e)}")
            db.rollback()
            cursor.close()
            return jsonify({"error": "Failed to create Persona"}), 500

    def create_personas(self):
        db = get_db()
        cursor = db.cursor()

        try:
            data = request.get_json()

            if not isinstance(data, list):
                return (
                    jsonify(
                        {"error": "Invalid data format. Expected a list of personas"}
                    ),
                    400,
                )

            for persona_data in data:
                name = persona_data.get("name")

                cursor.execute(
                    "SELECT id FROM Personas WHERE lower(name) = lower(%s)", (name,)
                )
                existing_persona = cursor.fetchone()

                if existing_persona:
                    return (
                        jsonify({"error": f"A persona named '{name}' already exists"}),
                        400,
                    )

                inherits = persona_data.get("inherits")
                item = persona_data.get("item")
                itemr = persona_data.get("itemr")
                lvl = persona_data.get("lvl")
                trait = persona_data.get("trait")
                arcana = persona_data.get("arcana")

                cursor.execute(
                    """INSERT INTO Personas 
                  (name, inherits, item, itemr, lvl, trait, arcana) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (name, inherits, item, itemr, lvl, trait, arcana),
                )

                persona_id = 0
                row = cursor.fetchone()
                if row is None:
                    return (
                        jsonify({"error": "An error occurred on our side"}),
                        500,
                    )
                else:
                    persona_id = row[0]

                resistances = persona_data.get("resists", {})
                cursor.execute(
                    """INSERT INTO PersonaResistances 
                    (persona_id, phys, gun, fire, ice, 
                    elec, wind, pys, nuke, bless, curse) 
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        persona_id,
                        resistances.get("phys", ""),
                        resistances.get("gun", ""),
                        resistances.get("fire", ""),
                        resistances.get("ice", ""),
                        resistances.get("elec", ""),
                        resistances.get("wind", ""),
                        resistances.get("pys", ""),
                        resistances.get("nuke", ""),
                        resistances.get("bless", ""),
                        resistances.get("curse", ""),
                    ),
                )

                skills = persona_data.get("skills", {})
                for skill_name, level in skills.items():
                    cursor.execute(
                        """INSERT INTO PersonaSkills (persona_id, name, level) 
                      VALUES (%s, %s, %s)""",
                        (persona_id, skill_name, level),
                    )

                stats = persona_data.get("stats", {})
                cursor.execute(
                    """INSERT INTO PersonaStats (persona_id, st, ma, en, ag, lu) 
                  VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        persona_id,
                        stats.get("st", 0),
                        stats.get("ma", 0),
                        stats.get("en", 0),
                        stats.get("ag", 0),
                        stats.get("lu", 0),
                    ),
                )

            db.commit()
            cursor.close()

            return jsonify({"message": "Personas created successfully"}), 201
        except Exception as e:
            print(f"Error creating Personas: {str(e)}")
            db.rollback()
            cursor.close()
            return jsonify({"error": "Failed to create Personas"}), 500

    def delete_persona_by_name(self, name: str):
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("SELECT * FROM Personas WHERE name = %s", (name,))
            persona = cursor.fetchone()

            if not persona:
                return jsonify({"error": "Persona not found"}), 404

            # Deleting from associated tables first to maintain referential integrity
            persona_id = persona[0]
            cursor.execute(
                "DELETE FROM PersonaResistances WHERE persona_id = %s", (persona_id,)
            )
            cursor.execute(
                "DELETE FROM PersonaSkills WHERE persona_id = %s", (persona_id,)
            )
            cursor.execute(
                "DELETE FROM PersonaStats WHERE persona_id = %s", (persona_id,)
            )

            # Then deleting it from the Personas table
            cursor.execute("DELETE FROM Personas WHERE id = %s", (persona_id,))

            db.commit()
            cursor.close()

            return jsonify({"message": f"Persona '{name}' deleted successfully"}), 200
        except Exception as e:
            print(f"Error deleting Persona: {str(e)}")
            db.rollback()
            cursor.close()
            return jsonify({"error": "Failed to delete Persona"}), 500

    def update_persona_by_name(self, name: str):
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                "SELECT * FROM Personas WHERE lower(name) = lower(%s)", (name,)
            )
            persona = cursor.fetchone()

            if not persona:
                return jsonify({"error": "Persona not found"}), 404

            data = request.get_json()

            inherits = data.get("inherits", persona[2])
            item = data.get("item", persona[3])
            itemr = data.get("itemr", persona[4])
            lvl = data.get("lvl", persona[5])
            trait = data.get("trait", persona[6])
            arcana = data.get("arcana", persona[7])

            cursor.execute(
                """UPDATE Personas SET inherits = %s, item = %s, itemr = %s, lvl = %s, 
              trait = %s, arcana = %s WHERE id = %s""",
                (inherits, item, itemr, lvl, trait, arcana, persona[0]),
            )

            db.commit()
            cursor.close()

            return jsonify({"message": f"Persona '{name}' updated successfully"}), 200
        except Exception as e:
            print(f"Error updating Persona: {str(e)}")
            db.rollback()
            cursor.close()
            return jsonify({"error": "Failed to update Persona"}), 500

    def __get_resists_for_persona(self, cursor, persona_id: int) -> Dict[str, Any]:
        cursor.execute(
            "SELECT * FROM PersonaResistances WHERE persona_id = %s", (persona_id,)
        )
        resists = cursor.fetchone()

        if resists:
            return {
                "phys": resists[2],
                "gun": resists[3],
                "fire": resists[4],
                "ice": resists[5],
                "elec": resists[6],
                "wind": resists[7],
                "pys": resists[8],
                "nuke": resists[9],
                "bless": resists[10],
                "curse": resists[11],
            }
        else:
            return {}

    def __skill_tuple_to_dict(self, skill_tuple) -> Dict[str, Any]:
        return {
            "id": skill_tuple[0],
            "element": skill_tuple[1],
            "name": skill_tuple[2],
            "cost": skill_tuple[3],
            "effect": skill_tuple[4],
            "target": skill_tuple[5],
        }

    def __get_skills_for_persona(self, cursor, persona_id: int) -> Dict[str, Any]:
        cursor.execute(
            "SELECT * FROM PersonaSkills WHERE persona_id = %s", (persona_id,)
        )
        skills = cursor.fetchall()

        skills_dict = {}
        for skill in skills:
            skills_dict[skill[2]] = skill[3]

        return skills_dict

    def __get_skills_for_persona_by_name(self, cursor, persona_name: str) -> List[str]:
        cursor.execute(
            """
            SELECT PersonaSkills.name
            FROM Personas
            JOIN PersonaSkills ON Personas.id = PersonaSkills.persona_id
            WHERE Personas.name = %s
            """,
            (persona_name,),
        )

        skills = cursor.fetchall()
        skills_list = [skill[0] for skill in skills]

        detailed_skills = []
        for skill_name in skills_list:
            cursor.execute(
                """
                SELECT *
                FROM Skills
                WHERE name = %s
                """,
                (skill_name,),
            )
            skill_data = cursor.fetchone()
            if skill_data:
                skill_dict = self.__skill_tuple_to_dict(skill_data)
                detailed_skills.append(skill_dict)

        return detailed_skills

    def __get_stats_for_persona(self, cursor, persona_id) -> Dict[str, int]:
        cursor.execute(
            "SELECT * FROM PersonaStats WHERE persona_id = %s", (persona_id,)
        )
        stats = cursor.fetchone()

        if stats:
            return {
                "st": stats[2],
                "ma": stats[3],
                "en": stats[4],
                "ag": stats[5],
                "lu": stats[6],
            }
        else:
            return {}
