import click
import os
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


@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()


def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
