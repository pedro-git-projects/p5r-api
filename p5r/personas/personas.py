from typing import Any, Dict, List
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from p5r.db import get_db


class PersonaBlueprint:
    def __init__(self, name: str, import_name: str) -> None:
        self.blueprint = Blueprint(name, import_name)
        self.setup_routes()

    def setup_routes(self):
        self.blueprint.route("/personas", methods=["GET"])(self.get_all_personas)
        self.blueprint.route("/personas", methods=["POST"])(
            jwt_required()(self.create_persona)
        )
        self.blueprint.route("/personas/many", methods=["POST"])(
            jwt_required()(self.create_personas)
        )
        self.blueprint.route("/personas/exact/<string:name>", methods=["GET"])(
            self.get_persona_by_exact_name
        )
        self.blueprint.route("/personas/<string:name>", methods=["GET"])(
            self.get_personas_by_partial_name
        )
        self.blueprint.route("/personas/detailed/<string:name>", methods=["GET"])(
            self.get_detailed_persona_by_name
        )

        self.blueprint.route("/personas/<string:name>", methods=["DELETE"])(
            jwt_required()(self.delete_persona_by_name)
        )
        self.blueprint.route("/personas/<string:name>", methods=["PUT"])(
            jwt_required()(self.update_persona_by_name)
        )

    def get_all_personas(self):
        """
        Get all personas
        ---
        tags:
          - Personas
        responses:
          200:
            description: List of personas
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: The unique identifier for the persona.
                  name:
                    type: string
                    description: The name of the persona (e.g., "Abaddon").
                  inherits:
                    type: string
                    description: The type of damage the persona inherits (e.g., "curse").

                  item:
                    type: string
                    description: The item associated with the persona (e.g., "Megaton Raid Belt").
                  itemr:
                    type: string
                    description: The rare item associated with the persona (e.g., "God's Hand Belt").
                  lvl:
                    type: integer
                    description: The level of the persona (e.g., 75).
                  trait:
                    type: string
                    description: The trait of the persona (e.g., "Mouth of Savoring").
                  arcana:
                    type: string
                    description: The arcana associated with the persona (e.g., "Judgement").
                  rare:
                    type: boolean
                    description: Indicates whether the persona is rare (e.g., false).
                  special:
                    type: boolean
                    description: Indicates whether the persona has special characteristics (e.g., false).
                  resists:
                    type: object
                    description: Resistances of the persona to various damage types.
                    example:
                      bless: "s"
                      curse: "d"
                      elec: "-"
                      fire: "-"
                      gun: "d"
                      ice: "-"
                      nuke: "-"
                      phys: "d"
                      pys: "-"
                      wind: "-"
                  skills:
                    type: object
                    description: Skills possessed by the persona and their corresponding levels.
                    example:
                      "Absorb Phys": 80
                      "Ailment Boost": 79
                      "Enduring Soul": 0
                      "Flash Bomb": 78
                      "Gigantomachia": 81
                      "Mabufudyne": 0
                      "Megaton Raid": 0
                  stats:
                    type: object
                    description: Base stats of the persona.
                    example:
                      ag: 38
                      en: 58
                      lu: 43
                      ma: 42
                      st: 51
        """  # noqa: E501
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
                "rare": persona[8],
                "special": persona[9],
                "resists": self.__get_resists_for_persona(cursor, persona[0]),
                "skills": self.__get_skills_for_persona(cursor, persona[0]),
                "stats": self.__get_stats_for_persona(cursor, persona[0]),
            }
            personas_list.append(persona_dict)

        cursor.close()

        return jsonify(personas_list)

    def get_persona_by_exact_name(self, name: str):
        """
        Get persona by exact name
        ---
        tags:
          - Personas
        parameters:
          - name: name
            in: path
            type: string
            required: true
            description: The exact name of the persona to search for.
        responses:
          200:
            description: Persona details
            schema:
              type: object
              properties:
                id:
                  type: integer
                  description: The unique identifier for the persona.
                name:
                  type: string
                  description: The name of the persona.
                inherits:
                  type: string
                  description: The type of damage the persona inherits.
                item:
                  type: string
                  description: The item associated with the persona.
                itemr:
                  type: string
                  description: The rare item associated with the persona.
                lvl:
                  type: integer
                  description: The level of the persona.
                trait:
                  type: string
                  description: The trait of the persona.
                arcana:
                  type: string
                  description: The arcana associated with the persona.
                rare:
                  type: boolean
                  description: Indicates whether the persona is rare.
                special:
                  type: boolean
                  description: Indicates whether the persona has special characteristics.
                resists:
                  type: object
                  description: Resistances of the persona to various damage types.
                  example:
                    bless: "s"
                    curse: "d"
                    elec: "-"
                    fire: "-"
                    gun: "d"
                    ice: "-"
                    nuke: "-"
                    phys: "d"
                    pys: "-"
                    wind: "-"
                skills:
                  type: object
                  description: Skills possessed by the persona and their corresponding levels.
                  example:
                    "Absorb Phys": 80
                    "Ailment Boost": 79
                    "Enduring Soul": 0
                    "Flash Bomb": 78
                    "Gigantomachia": 81
                    "Mabufudyne": 0
                    "Megaton Raid": 0
                stats:
                  type: object
                  description: Base stats of the persona.
                  example:
                    ag: 38
                    en: 58
                    lu: 43
                    ma: 42
                    st: 51
          404:
            description: Persona not found
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating that the persona was not found.
        """  # noqa: E501

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM Personas WHERE lower(name) = lower(%s)",
            (name,),
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
            "rare": persona[8],
            "special": persona[9],
            "resists": self.__get_resists_for_persona(cursor, persona[0]),
            "skills": self.__get_skills_for_persona(cursor, persona[0]),
            "stats": self.__get_stats_for_persona(cursor, persona[0]),
        }

        cursor.close()

        return jsonify(persona_dict)

    def get_personas_by_partial_name(self, name: str):
        """
        Get personas by name (partial match)
        ---
        tags:
          - Personas
        parameters:
          - name: name
            in: path
            type: string
            required: true
            description: The name of the persona to search for.
        responses:
          200:
            description: List of persona details
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: The unique identifier for the persona.
                  name:
                    type: string
                    description: The name of the persona.
                  inherits:
                    type: string
                    description: The type of damage the persona inherits.
                  item:
                    type: string
                    description: The item associated with the persona.
                  itemr:
                    type: string
                    description: The rare item associated with the persona.
                  lvl:
                    type: integer
                    description: The level of the persona.
                  trait:
                    type: string
                    description: The trait of the persona.
                  arcana:
                    type: string
                    description: The arcana associated with the persona.
                  rare:
                    type: boolean
                    description: Indicates whether the persona is rare.
                  special:
                    type: boolean
                    description: Indicates whether the persona has special characteristics.
                  resists:
                    type: object
                    description: Resistances of the persona to various damage types.
                    example:
                      bless: "s"
                      curse: "d"
                      elec: "-"
                      fire: "-"
                      gun: "d"
                      ice: "-"
                      nuke: "-"
                      phys: "d"
                      pys: "-"
                      wind: "-"
                  skills:
                    type: object
                    description: Skills possessed by the persona and their corresponding levels.
                    example:
                      "Absorb Phys": 80
                      "Ailment Boost": 79
                      "Enduring Soul": 0
                      "Flash Bomb": 78
                      "Gigantomachia": 81
                      "Mabufudyne": 0
                      "Megaton Raid": 0
                  stats:
                    type: object
                    description: Base stats of the persona.
                    example:
                      ag: 38
                      en: 58
                      lu: 43
                      ma: 42
                      st: 51
          404:
            description: Persona not found
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating that the persona was not found.
        """  # noqa: E501

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM Personas WHERE lower(name) LIKE lower(%s)",
            ("%" + name + "%",),
        )
        personas = cursor.fetchall()

        if not personas:
            return jsonify({"error": "Persona not found"}), 404

        persona_list = []
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
                "rare": persona[8],
                "special": persona[9],
                "resists": self.__get_resists_for_persona(cursor, persona[0]),
                "skills": self.__get_skills_for_persona(cursor, persona[0]),
                "stats": self.__get_stats_for_persona(cursor, persona[0]),
            }
            persona_list.append(persona_dict)

        cursor.close()

        return jsonify(persona_list)

    def get_detailed_persona_by_name(self, name: str):
        """
        Get detailed persona by name
        ---
        tags:
          - Personas
        parameters:
          - name: name
            in: path
            type: string
            required: true
            description: The name of the persona to search for.
        responses:
          200:
            description: Persona details
            schema:
              type: object
              properties:
                id:
                  type: integer
                  description: The unique identifier for the persona.
                name:
                  type: string
                  description: The name of the persona.
                inherits:
                  type: string
                  description: The type of damage the persona inherits.
                item:
                  type: string
                  description: The item associated with the persona.
                itemr:
                  type: string
                  description: The rare item associated with the persona.
                lvl:
                  type: integer
                  description: The level of the persona.
                trait:
                  type: string
                  description: The trait of the persona.
                arcana:
                  type: string
                  description: The arcana associated with the persona.
                resists:
                  type: object
                  description: Resistances of the persona to various damage types.
                  example:
                    bless: "s"
                    curse: "d"
                    elec: "-"
                    fire: "-"
                    gun: "d"
                    ice: "-"
                    nuke: "-"
                    phys: "d"
                    pys: "-"
                    wind: "-"
                skills:
                  type: object
                  description: Skills possessed by the persona and their corresponding levels.
                  example:
                    "Absorb Phys": 80
                    "Ailment Boost": 79
                    "Enduring Soul": 0
                    "Flash Bomb": 78
                    "Gigantomachia": 81
                    "Mabufudyne": 0
                    "Megaton Raid": 0
                detailed_skills:
                  type: object
                  description: Detailed skills for the persona.
                  example:
                    "Megaton Raid": "Heavy Phys damage to 1 foe."
                    "Enduring Soul": "Survive one lethal attack with 1 HP remaining."
                    "Gigantomachia": "Colossal Phys damage to 1 foe."
                stats:
                  type: object
                  description: Base stats of the persona.
                  example:
                    ag: 38
                    en: 58
                    lu: 43
                    ma: 42
                    st: 51
          404:
            description: Persona not found
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating that the persona was not found.
        """  # noqa: E501

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
        """
        Create a new persona
        ---
        tags:
          - Personas
        consumes:
          - application/json
        parameters:
          - in: body
            name: persona
            description: Persona data to create a new persona
            required: true
            schema:
              type: object
              properties:
                name:
                  type: string
                  description: The name of the persona.
                inherits:
                  type: string
                  description: The type of damage the persona inherits.
                item:
                  type: string
                  description: The item associated with the persona.
                itemr:
                  type: string
                  description: The rare item associated with the persona.
                lvl:
                  type: integer
                  description: The level of the persona.
                trait:
                  type: string
                  description: The trait of the persona.
                arcana:
                  type: string
                  description: The arcana associated with the persona.
                rare:
                  type: boolean
                  description: Indicates whether the persona is rare.
                special:
                  type: boolean
                  description: Indicates whether the persona has special characteristics.
                resists:
                  type: object
                  description: Resistances of the persona to various damage types.
                  example:
                    bless: "s"
                    curse: "d"
                    elec: "-"
                    fire: "-"
                    gun: "d"
                    ice: "-"
                    nuke: "-"
                    phys: "d"
                    pys: "-"
                    wind: "-"
                skills:
                  type: object
                  description: Skills possessed by the persona and their corresponding levels.
                  example:
                    "Absorb Phys": 80
                    "Ailment Boost": 79
                    "Enduring Soul": 0
                    "Flash Bomb": 78
                    "Gigantomachia": 81
                    "Mabufudyne": 0
                    "Megaton Raid": 0
                stats:
                  type: object
                  description: Base stats of the persona.
                  example:
                    ag: 38
                    en: 58
                    lu: 43
                    ma: 42
                    st: 51
        responses:
          201:
            description: Persona created successfully
            schema:
              type: object
              properties:
                id:
                  type: integer
                  description: The unique identifier for the created persona.
          400:
            description: Bad request. A persona with the same name already exists.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the persona already exists.
          401:
            description: Unauthorized. Missing or invalid token.
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
          500:
            description: Internal Server Error. Failed to create persona.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the failure to create persona.
        """  # noqa: E501

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
            rare = data.get("rare", False)
            special = data.get("special", False)
            cursor.execute(
                """INSERT INTO Personas 
                  (name, inherits, item, itemr, lvl, trait, arcana, rare, special) 
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (name, inherits, item, itemr, lvl, trait, arcana, rare, special),
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
        """
        Create multiple personas
        ---
        tags:
          - Personas
        consumes:
          - application/json
        parameters:
          - in: body
            name: personas
            description: List of personas to create
            required: true
            schema:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                    description: The name of the persona.
                  inherits:
                    type: string
                    description: The type of damage the persona inherits.
                  item:
                    type: string
                    description: The item associated with the persona.
                  itemr:
                    type: string
                    description: The rare item associated with the persona.
                  lvl:
                    type: integer
                    description: The level of the persona.
                  trait:
                    type: string
                    description: The trait of the persona.
                  arcana:
                    type: string
                    description: The arcana associated with the persona.
                  rare:
                    type: boolean
                    description: Indicates whether the persona is rare.
                  special:
                    type: boolean
                    description: Indicates whether the persona has special characteristics.
                  resists:
                    type: object
                    description: Resistances of the persona to various damage types.
                    example:
                      bless: "s"
                      curse: "d"
                      elec: "-"
                      fire: "-"
                      gun: "d"
                      ice: "-"
                      nuke: "-"
                      phys: "d"
                      pys: "-"
                      wind: "-"
                  skills:
                    type: object
                    description: Skills possessed by the persona and their corresponding levels.
                    example:
                      "Absorb Phys": 80
                      "Ailment Boost": 79
                      "Enduring Soul": 0
                      "Flash Bomb": 78
                      "Gigantomachia": 81
                      "Mabufudyne": 0
                      "Megaton Raid": 0
                  stats:
                    type: object
                    description: Base stats of the persona.
                    example:
                      ag: 38
                      en: 58
                      lu: 43
                      ma: 42
                      st: 51
        responses:
          201:
            description: Personas created successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: A success message indicating the personas were created successfully.
          400:
            description: Bad request. Invalid data format or a persona with the same name already exists.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the issue with the request.
          401:
            description: Unauthorized. Missing or invalid token.
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
          500:
            description: Internal Server Error. Failed to create personas.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the failure to create personas.
        """  # noqa: E501

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
                rare = persona_data.get("rare", False)
                special = persona_data.get("special", False)

                cursor.execute(
                    """INSERT INTO Personas 
                  (name, inherits, item, itemr, lvl, trait, arcana, rare, special) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (name, inherits, item, itemr, lvl, trait, arcana, rare, special),
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
        """
        Delete a persona by name
        ---
        tags:
          - Personas
        parameters:
          - name: name
            in: path
            type: string
            required: true
            description: The name of the persona to delete.
        responses:
          200:
            description: Persona deleted successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: A success message indicating the deletion of the persona.

          401:
            description: Unauthorized. Missing or invalid token.
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
          404:
            description: Persona not found.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating that the persona was not found.
          500:
            description: Internal Server Error. Failed to delete persona.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the failure to delete persona.
        """  # noqa: E501

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
        """
        Update a persona by name
        ---
        tags:
          - Personas
        parameters:
          - name: name
            in: path
            type: string
            required: true
            description: The name of the persona to update.
          - in: body
            name: persona_data
            description: Data to update for the persona
            required: true
            schema:
              type: object
              properties:
                inherits:
                  type: string
                  description: The type of damage the persona inherits.
                item:
                  type: string
                  description: The item associated with the persona.
                itemr:
                  type: string
                  description: The rare item associated with the persona.
                lvl:
                  type: integer
                  description: The level of the persona.
                trait:
                  type: string
                  description: The trait of the persona.
                arcana:
                  type: string
                  description: The arcana associated with the persona.
        responses:
          200:
            description: Persona updated successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: A success message indicating the update of the persona.
          401:
            description: Unauthorized. Missing or invalid token.
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
          404:
            description: Persona not found.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating that the persona was not found.
          500:
            description: Internal Server Error. Failed to update persona.
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating the failure to update persona.
        """

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
