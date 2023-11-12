from flask import Blueprint, jsonify, request
from p5r.db import get_db

persona_bp = Blueprint("personas", __name__)


@persona_bp.route("/personas", methods=["GET"])
def get_all_personas():
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
            "resists": get_resists_for_persona(cursor, persona[0]),
            "skills": get_skills_for_persona(cursor, persona[0]),
            "stats": get_stats_for_persona(cursor, persona[0]),
        }
        personas_list.append(persona_dict)

    cursor.close()

    return jsonify(personas_list)


@persona_bp.route("/personas/<string:name>", methods=["GET"])
def get_persona_by_name(name):
    db = get_db()
    cursor = db.cursor()

    # Using ILIKE for case-insensitive and partial matching
    cursor.execute(
        "SELECT * FROM Personas WHERE lower(name) LIKE lower(%s)", ("%" + name + "%",)
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
        "resists": get_resists_for_persona(cursor, persona[0]),
        "skills": get_skills_for_persona(cursor, persona[0]),
        "stats": get_stats_for_persona(cursor, persona[0]),
    }

    cursor.close()

    return jsonify(persona_dict)


def get_resists_for_persona(cursor, persona_id):
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


def get_skills_for_persona(cursor, persona_id):
    cursor.execute("SELECT * FROM PersonaSkills WHERE persona_id = %s", (persona_id,))
    skills = cursor.fetchall()

    skills_dict = {}
    for skill in skills:
        skills_dict[skill[2]] = skill[3]

    return skills_dict


def get_stats_for_persona(cursor, persona_id):
    cursor.execute("SELECT * FROM PersonaStats WHERE persona_id = %s", (persona_id,))
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


@persona_bp.route("/personas", methods=["POST"])
def create_persona():
    db = get_db()
    cursor = db.cursor()

    try:
        data = request.get_json()

        name = data["name"]

        # Check if the persona with the same name already exists
        cursor.execute("SELECT id FROM Personas WHERE lower(name) = lower(%s)", (name,))
        existing_persona = cursor.fetchone()

        if existing_persona:
            return (
                jsonify({"error": f"A persona with the name '{name}' already exists"}),
                400,
            )

        inherits = data["inherits"]
        item = data["item"]
        itemr = data["itemr"]
        lvl = data["lvl"]
        trait = data["trait"]
        arcana = data["arcana"]

        cursor.execute(
            """INSERT INTO Personas (name, inherits, item, itemr, lvl, trait, arcana) 
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


@persona_bp.route("/skills", methods=["GET"])
def get_all_skills():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM Skills")
    skills = cursor.fetchall()

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

    cursor.close()

    return jsonify(skills_list)


@persona_bp.route("/personas/<string:name>", methods=["DELETE"])
def delete_persona_by_name(name):
    db = get_db()
    cursor = db.cursor()

    try:
        # Checking if the persona exists
        cursor.execute("SELECT * FROM Personas WHERE name = %s", (name,))
        persona = cursor.fetchone()

        if not persona:
            return jsonify({"error": "Persona not found"}), 404

        # Deleting from the associated tables first to maintain referential integrity
        persona_id = persona[0]
        cursor.execute(
            "DELETE FROM PersonaResistances WHERE persona_id = %s", (persona_id,)
        )
        cursor.execute("DELETE FROM PersonaSkills WHERE persona_id = %s", (persona_id,))
        cursor.execute("DELETE FROM PersonaStats WHERE persona_id = %s", (persona_id,))

        # Then delete from the Personas table
        cursor.execute("DELETE FROM Personas WHERE id = %s", (persona_id,))

        db.commit()
        cursor.close()

        return jsonify({"message": f"Persona '{name}' deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting Persona: {str(e)}")
        db.rollback()
        cursor.close()
        return jsonify({"error": "Failed to delete Persona"}), 500


@persona_bp.route("/personas/<string:name>", methods=["PUT"])
def update_persona_by_name(name):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT * FROM Personas WHERE lower(name) = lower(%s)", (name,))
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
