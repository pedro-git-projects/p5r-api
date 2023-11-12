from flask import Flask
from dotenv import load_dotenv
from flasgger import Swagger
import os


load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE_URL=os.environ.get("DATABASE_URL"),
        SWAGGER={
            "title": "Persona 5 Royal API",
            "uiversion": 3,
            "version": 1.0,
            "description": "Compendium and fusion calculator for persona 5 royal.",
            "tags": [],
        },
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db

    db.init_app(app)

    from p5r.personas import persona_bp
    from p5r.skills import skills_bp

    app.register_blueprint(persona_bp)
    app.register_blueprint(skills_bp)

    Swagger(app)

    return app
