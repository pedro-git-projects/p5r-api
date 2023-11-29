from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS
from flasgger import Swagger
from flask_jwt_extended import JWTManager
import os


load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE_URL=os.environ.get("DATABASE_URL"),
        JWT_SECRET=os.environ.get("JWT_SECRET"),
        SWAGGER={
            "title": "Persona 5 Royal API",
            "uiversion": 3,
            "description": "Compendium and fusion calculator API for persona 5 royal",
            "contact": {
                "url": "https://github.com/pedro-git-projects",
            },
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

    from p5r.personas.personas import PersonaBlueprint
    from p5r.skills.skills import SkillsBlueprint
    from p5r.calculator.fusion import FusionCalculatorBlueprint
    from p5r.users.users import UsersBlueprint

    app.register_blueprint(PersonaBlueprint("pesonas", __name__).blueprint)
    app.register_blueprint(SkillsBlueprint("skills", __name__).blueprint)
    app.register_blueprint(FusionCalculatorBlueprint("calculator", __name__).blueprint)
    app.register_blueprint(UsersBlueprint("users", __name__).blueprint)

    jwt = JWTManager(app)  # noqa: F841
    CORS(app, resources={r"/*": {"origins": "*"}})
    Swagger(app, template=app.config["SWAGGER"])

    return app
