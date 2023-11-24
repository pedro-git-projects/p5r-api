import click
import os
import json
from flask import Flask, current_app, g
from dotenv import load_dotenv
import psycopg2


load_dotenv()


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            host="localhost",
            dbname=os.environ.get("POSTGRES_DB"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD"),
        )

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        commands = f.read().decode("utf-8")
        cur = db.cursor()
        cur.execute(commands)
        cur.close()
        db.commit()

    with current_app.open_resource("../data/skills.json") as f:
        skills_data = json.load(f)
        cur = db.cursor()
        for skill in skills_data:
            cur.execute(
                """INSERT INTO Skills (element, name, cost, effect, target) 
                VALUES (%s, %s, %s, %s, %s)""",
                (
                    skill["element"],
                    skill["name"],
                    skill["cost"],
                    skill["effect"],
                    skill["target"],
                ),
            )
        cur.close()
        db.commit()

    with current_app.open_resource("../data/personas.json") as f:
        personas_data = json.load(f)
        cur = db.cursor()
        for persona in personas_data:
            # Insert persona data
            cur.execute(
                """INSERT INTO Personas 
                (name, inherits, item, itemr, lvl, trait, arcana, rare, special) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    persona["name"],
                    persona["inherits"],
                    persona["item"],
                    persona["itemr"],
                    persona["lvl"],
                    persona["trait"],
                    persona["arcana"],
                    persona["rare"],
                    persona["special"],
                ),
            )

            result = cur.fetchone()
            if result is not None:
                persona_id = result[0]

                resistances = persona.get("resists", {})
                cur.execute(
                    """INSERT INTO PersonaResistances 
                    (persona_id, phys, gun, fire, ice, elec, 
                    wind, pys, nuke, bless, curse) 
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

                skills = persona.get("skills", {})
                for skill_name, skill_level in skills.items():
                    cur.execute(
                        """INSERT INTO PersonaSkills (persona_id, name, level) 
                        VALUES (%s, %s, %s)""",
                        (persona_id, skill_name, skill_level),
                    )

                stats = persona.get("stats", {})
                cur.execute(
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

        cur.close()
        db.commit()


@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()


def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
